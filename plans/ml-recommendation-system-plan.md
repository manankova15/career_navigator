# План внедрения ML-модели для рекомендательной системы Career Navigator

## 1. Анализ текущей архитектуры

### Текущее состояние (Phase 1)
Ваша система использует **content-based подход** с rule-based скорингом:

**Компоненты:**
- [`ml-service`](../services/ml-service/app/scoring.py) — вычисляет взвешенный скор на основе:
  - Навыков (Jaccard similarity): 50%
  - Локации: 20%
  - Зарплаты: 15%
  - Уровня (seniority): 15%
- [`recommendation-service`](../services/recommendation-service/app/orchestrator.py) — оркестрирует процесс:
  1. Получает профиль пользователя
  2. Загружает вакансии
  3. Вызывает ml-service для скоринга
  4. Сохраняет результаты в БД
  5. Вычисляет skill gaps

**Преимущества текущего подхода:**
- ✅ Простой и понятный
- ✅ Не требует обучающих данных
- ✅ Работает с первого дня
- ✅ Легко объяснить пользователю

**Недостатки:**
- ❌ Не учитывает поведение пользователей
- ❌ Статические веса не адаптируются
- ❌ Нет персонализации на основе истории
- ❌ Не использует collaborative filtering

---

## 2. Требования и ограничения для ML модели

### Функциональные требования
1. **Персонализация** — учет индивидуальных предпочтений пользователя
2. **Обучение на feedback** — использование откликов (positive/negative/saved)
3. **Cold start** — работа для новых пользователей без истории
4. **Explainability** — возможность объяснить, почему вакансия рекомендована
5. **Real-time inference** — скоринг за < 500ms для 300 вакансий

### Нефункциональные требования
1. **Простота** — модель должна быть понятной и поддерживаемой
2. **Масштабируемость** — работа с растущим числом пользователей
3. **Offline training** — обучение не должно блокировать продакшн
4. **A/B testing** — возможность сравнения с baseline

### Доступные данные
**Профиль пользователя:**
- Навыки (skills) с уровнем владения
- Предпочтения (локация, зарплата, формат работы, роли)
- Опыт работы (компании, должности, даты)
- Образование
- Уровень (seniority)

**Вакансии:**
- Название, компания, описание
- Требуемые навыки
- Локация, зарплата, тип занятости
- Уровень (seniority)

**Поведенческие данные:**
- Feedback на рекомендации (positive/negative/saved)
- История просмотров (через analytics-service)
- Результаты тестирований (assessment-service)

**Ограничения:**
- Малое количество данных на старте (cold start problem)
- Нет истории кликов/откликов для большинства пользователей
- Нужна быстрая инференция (real-time)

---

## 3. Рекомендуемый подход: Hybrid Recommendation System

### Архитектура: Two-Stage Ranking

```
┌─────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION PIPELINE                   │
└─────────────────────────────────────────────────────────────┘

Stage 1: CANDIDATE GENERATION (Fast Filtering)
┌──────────────────────────────────────────────────────────────┐
│  Content-Based Filter (текущий подход)                       │
│  • Фильтрация по локации, зарплате, seniority               │
│  • Базовый skill matching                                    │
│  • Результат: ~300 кандидатов                                │
└──────────────────────────────────────────────────────────────┘
                            ↓
Stage 2: RANKING (ML Model)
┌──────────────────────────────────────────────────────────────┐
│  Hybrid ML Ranker                                             │
│  ┌────────────────────┐  ┌─────────────────────────────┐    │
│  │ Content Features   │  │ Collaborative Features      │    │
│  │ • Skill similarity │  │ • User behavior history     │    │
│  │ • Salary match     │  │ • Similar users preferences │    │
│  │ • Location score   │  │ • Vacancy popularity        │    │
│  │ • Seniority match  │  │ • Assessment results        │    │
│  └────────────────────┘  └─────────────────────────────┘    │
│                            ↓                                  │
│              ┌──────────────────────────┐                    │
│              │  LightGBM Ranker Model   │                    │
│              │  (Learning to Rank)      │                    │
│              └──────────────────────────┘                    │
│                            ↓                                  │
│              Ranked Top-N Recommendations                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Выбор алгоритма: LightGBM для Learning-to-Rank

### Почему LightGBM?

**Преимущества:**
1. ✅ **Быстрый** — inference за миллисекунды
2. ✅ **Простой** — не требует сложной инфраструктуры (в отличие от нейросетей)
3. ✅ **Эффективный** — работает с малым количеством данных
4. ✅ **Интерпретируемый** — feature importance для explainability
5. ✅ **Встроенная поддержка ranking** — LambdaRank objective
6. ✅ **Легко обновлять** — инкрементальное обучение

**Альтернативы (не рекомендую для старта):**
- ❌ **Deep Learning** (Neural Collaborative Filtering) — требует много данных и GPU
- ❌ **Matrix Factorization** (ALS, SVD) — плохо работает с cold start
- ❌ **Graph Neural Networks** — слишком сложно для вашего случая

### Learning-to-Rank подход

**Задача:** Ранжировать вакансии для каждого пользователя

**Целевая переменная:**
- `1` — positive feedback (saved, applied)
- `0` — negative feedback или no interaction
- Можно использовать weighted labels (saved = 2, positive = 1, view = 0.5)

**Метрика качества:**
- NDCG@10 (Normalized Discounted Cumulative Gain)
- MAP@10 (Mean Average Precision)
- MRR (Mean Reciprocal Rank)

---

## 5. Feature Engineering

### Content-Based Features (20 признаков)

**Skill Features:**
```python
1. skill_jaccard_similarity      # Текущий подход
2. skill_intersection_count      # Количество совпадающих навыков
3. skill_missing_count           # Количество недостающих навыков
4. skill_weighted_match          # Учет уровня владения навыками
5. rare_skill_bonus              # Бонус за редкие навыки
```

**Salary Features:**
```python
6. salary_overlap_ratio          # Текущий подход
7. salary_gap_normalized         # Нормализованная разница
8. salary_above_expectation      # Зарплата выше ожиданий (boolean)
```

**Location Features:**
```python
9. location_exact_match          # Точное совпадение
10. location_is_remote           # Удаленная работа
11. location_distance_km         # Расстояние (если есть координаты)
```

**Seniority Features:**
```python
12. seniority_exact_match        # Точное совпадение
13. seniority_level_diff         # Разница в уровнях
14. seniority_is_promotion       # Вакансия на уровень выше
```

**Text Similarity:**
```python
15. title_similarity             # TF-IDF similarity заголовков
16. description_similarity       # TF-IDF similarity описаний
```

**Vacancy Metadata:**
```python
17. vacancy_age_days             # Возраст вакансии
18. company_size_category        # Размер компании (если есть)
19. employment_type_match        # Совпадение типа занятости
20. work_format_match            # Remote/office/hybrid match
```

### Collaborative Features (10 признаков)

**User Behavior:**
```python
21. user_total_interactions      # Общее количество взаимодействий
22. user_positive_rate           # Доля положительных откликов
23. user_avg_salary_viewed       # Средняя зарплата просмотренных вакансий
24. user_preferred_companies     # Предпочитаемые компании (embedding)
```

**Vacancy Popularity:**
```python
25. vacancy_view_count           # Количество просмотров
26. vacancy_positive_rate        # Доля положительных откликов
27. vacancy_avg_user_seniority   # Средний уровень заинтересованных пользователей
```

**Similar Users:**
```python
28. similar_users_liked          # Количество похожих пользователей, лайкнувших вакансию
29. similar_users_avg_score      # Средний скор от похожих пользователей
```

**Cross Features:**
```python
30. user_skill_vacancy_popularity # Популярность вакансии среди пользователей с похожими навыками
```

### Assessment Features (5 признаков)

```python
31. user_assessment_avg_score    # Средний балл по тестам
32. skill_gap_overlap            # Совпадение с выявленными пробелами
33. weak_skills_required         # Требуются слабые навыки пользователя
34. strong_skills_match          # Совпадение с сильными навыками
35. assessment_completion_rate   # Процент пройденных тестов
```

---

## 6. Архитектура решения

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                     ML-SERVICE (Enhanced)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  /ml/score (текущий endpoint)                                │
│  ├─ content_scorer.py      # Текущая логика (baseline)      │
│  └─ Returns: content-based scores                            │
│                                                               │
│  /ml/rank (новый endpoint) ⭐                                │
│  ├─ feature_extractor.py   # Извлечение признаков           │
│  ├─ lightgbm_ranker.py     # ML модель                      │
│  ├─ model_loader.py        # Загрузка модели из S3/MinIO    │
│  └─ Returns: ML-ranked scores + explanations                 │
│                                                               │
│  /ml/train (новый endpoint)                                  │
│  ├─ training_pipeline.py   # Обучение модели                │
│  ├─ feature_store.py       # Подготовка данных               │
│  └─ model_evaluator.py     # Оценка качества                │
│                                                               │
│  /ml/skill-gap (существующий)                                │
│  └─ skillgap.py            # Без изменений                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              RECOMMENDATION-SERVICE (Enhanced)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  orchestrator.py (обновленный)                               │
│  ├─ Шаг 1: Candidate generation (content-based)             │
│  ├─ Шаг 2: Feature enrichment (behavior, analytics)         │
│  ├─ Шаг 3: ML ranking (вызов /ml/rank)                      │
│  ├─ Шаг 4: Fallback to content-based (если ML недоступна)   │
│  └─ Шаг 5: Сохранение результатов + skill gaps              │
│                                                               │
│  feedback_collector.py (новый)                               │
│  └─ Сбор feedback для обучения модели                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ANALYTICS-SERVICE                         │
├─────────────────────────────────────────────────────────────┤
│  • Сбор событий (views, clicks, feedback)                   │
│  • Агрегация для collaborative features                      │
│  • Метрики качества рекомендаций (NDCG, CTR)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    TRAINING WORKER (новый)                   │
├─────────────────────────────────────────────────────────────┤
│  • Периодическое переобучение модели (weekly)                │
│  • Загрузка данных из PostgreSQL + ClickHouse               │
│  • Обучение LightGBM модели                                  │
│  • Оценка качества (offline metrics)                         │
│  • Сохранение модели в MinIO                                 │
│  • A/B тестирование (champion vs challenger)                │
└─────────────────────────────────────────────────────────────┘
```

### Хранение моделей

**MinIO (S3-compatible storage):**
```
s3://career-models/
├── lightgbm/
│   ├── production/
│   │   ├── model_v1.txt          # Текущая продакшн модель
│   │   ├── features_v1.json      # Список признаков
│   │   └── metadata_v1.json      # Метрики, дата обучения
│   ├── staging/
│   │   └── model_v2.txt          # Кандидат на замену
│   └── archive/
│       └── model_v0.txt          # Старые версии
└── embeddings/
    └── skill_embeddings.npy      # Для будущих улучшений
```

---

## 7. Поэтапный план внедрения

### Phase 2.1: Подготовка инфраструктуры (1-2 недели)

**Задачи:**
1. ✅ Добавить зависимости в [`ml-service/requirements.txt`](../services/ml-service/requirements.txt):
   ```
   lightgbm==4.3.0
   scikit-learn==1.4.0
   numpy==1.26.0
   pandas==2.2.0
   ```

2. ✅ Создать структуру для новых модулей:
   ```
   services/ml-service/app/
   ├── ranking/
   │   ├── __init__.py
   │   ├── feature_extractor.py    # Извлечение признаков
   │   ├── lightgbm_ranker.py      # ML модель
   │   ├── model_loader.py         # Загрузка из MinIO
   │   └── explainer.py            # Объяснение рекомендаций
   ├── training/
   │   ├── __init__.py
   │   ├── data_loader.py          # Загрузка обучающих данных
   │   ├── trainer.py              # Обучение модели
   │   └── evaluator.py            # Оценка качества
   └── routers/
       └── ranking.py              # Новые endpoints
   ```

3. ✅ Обновить [`recommendation-service/app/models.py`](../services/recommendation-service/app/models.py):
   - Добавить поле `algorithm_version` в `RecommendationSession`
   - Добавить поле `ml_score` в `VacancyRecommendation`
   - Добавить таблицу `UserFeedback` для сбора обучающих данных

4. ✅ Настроить MinIO bucket для моделей (уже есть в [`compose.yaml`](../compose.yaml))

### Phase 2.2: Baseline модель (2-3 недели)

**Задачи:**
1. ✅ Реализовать feature extraction:
   - Content-based features (20 признаков)
   - Использовать текущую логику из [`scoring.py`](../services/ml-service/app/scoring.py)

2. ✅ Создать синтетические обучающие данные:
   - Использовать текущий content-based скор как proxy для качества
   - Добавить шум для разнообразия
   - Цель: проверить pipeline, а не качество модели

3. ✅ Обучить первую LightGBM модель:
   - Objective: `lambdarank`
   - Metric: `ndcg@10`
   - Простая конфигурация (100 деревьев, depth=5)

4. ✅ Реализовать `/ml/rank` endpoint:
   - Извлечение признаков
   - Инференция модели
   - Fallback на content-based при ошибках

5. ✅ Обновить [`orchestrator.py`](../services/recommendation-service/app/orchestrator.py):
   - Добавить вызов `/ml/rank` после content-based фильтрации
   - Graceful degradation при недоступности ML

6. ✅ A/B тестирование:
   - 90% пользователей — content-based (control)
   - 10% пользователей — ML ranking (treatment)
   - Метрики: CTR, positive feedback rate, session duration

### Phase 2.3: Collaborative features (3-4 недели)

**Задачи:**
1. ✅ Реализовать сбор feedback:
   - Endpoint в recommendation-service для сохранения откликов
   - Интеграция с bot-service и frontend
   - Хранение в таблице `UserFeedback`

2. ✅ Добавить collaborative features:
   - User behavior features (4 признака)
   - Vacancy popularity features (3 признака)
   - Similar users features (2 признака)

3. ✅ Интеграция с analytics-service:
   - Получение статистики просмотров
   - Агрегация поведенческих данных

4. ✅ Переобучение модели на реальных данных:
   - Использовать собранный feedback
   - Оценить улучшение метрик

5. ✅ Расширить A/B тест:
   - 50% — content-based
   - 50% — ML ranking с collaborative features

### Phase 2.4: Assessment integration (2 недели)

**Задачи:**
1. ✅ Добавить assessment features (5 признаков)
2. ✅ Интеграция с assessment-service
3. ✅ Учет результатов тестов в ранжировании

### Phase 2.5: Production deployment (2 недели)

**Задачи:**
1. ✅ Создать training worker:
   - Celery task для еженедельного переобучения
   - Автоматическая оценка качества
   - Champion/Challenger pattern

2. ✅ Мониторинг и алерты:
   - Метрики качества (NDCG, MAP)
   - Latency инференции
   - Model drift detection

3. ✅ Документация:
   - API спецификация
   - Руководство по обучению модели
   - Troubleshooting guide

4. ✅ Полный rollout ML ranking для всех пользователей

---

## 8. Пример кода: Feature Extractor

```python
# services/ml-service/app/ranking/feature_extractor.py

from typing import Dict, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FeatureExtractor:
    """Извлечение признаков для ML ранжирования."""
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100, stop_words='english')
        
    def extract_content_features(
        self, 
        profile: Dict, 
        vacancy: Dict
    ) -> Dict[str, float]:
        """Извлечение content-based признаков."""
        
        user_skills = set(s.lower() for s in profile.get('skills', []))
        vac_skills = set(s.lower() for s in vacancy.get('skills', []))
        
        # Skill features
        intersection = user_skills & vac_skills
        union = user_skills | vac_skills
        
        features = {
            # Skill similarity
            'skill_jaccard': len(intersection) / len(union) if union else 0,
            'skill_intersection_count': len(intersection),
            'skill_missing_count': len(vac_skills - user_skills),
            
            # Salary features
            'salary_overlap_ratio': self._salary_overlap(profile, vacancy),
            'salary_above_expectation': self._salary_above(profile, vacancy),
            
            # Location features
            'location_exact_match': self._location_match(profile, vacancy),
            'location_is_remote': self._is_remote(vacancy),
            
            # Seniority features
            'seniority_exact_match': self._seniority_match(profile, vacancy),
            'seniority_level_diff': self._seniority_diff(profile, vacancy),
            
            # Vacancy metadata
            'vacancy_age_days': self._vacancy_age(vacancy),
        }
        
        return features
    
    def extract_collaborative_features(
        self,
        user_id: str,
        vacancy_id: str,
        user_stats: Dict,
        vacancy_stats: Dict
    ) -> Dict[str, float]:
        """Извлечение collaborative признаков."""
        
        features = {
            # User behavior
            'user_total_interactions': user_stats.get('total_interactions', 0),
            'user_positive_rate': user_stats.get('positive_rate', 0.5),
            
            # Vacancy popularity
            'vacancy_view_count': vacancy_stats.get('view_count', 0),
            'vacancy_positive_rate': vacancy_stats.get('positive_rate', 0.5),
            
            # Similar users (если есть данные)
            'similar_users_liked': vacancy_stats.get('similar_users_liked', 0),
        }
        
        return features
    
    def extract_all_features(
        self,
        profile: Dict,
        vacancy: Dict,
        user_stats: Dict = None,
        vacancy_stats: Dict = None
    ) -> np.ndarray:
        """Извлечение всех признаков для одной пары user-vacancy."""
        
        content_features = self.extract_content_features(profile, vacancy)
        
        if user_stats and vacancy_stats:
            collab_features = self.extract_collaborative_features(
                profile['user_id'],
                vacancy['vacancy_id'],
                user_stats,
                vacancy_stats
            )
            all_features = {**content_features, **collab_features}
        else:
            all_features = content_features
        
        # Преобразование в numpy array в фиксированном порядке
        feature_names = sorted(all_features.keys())
        feature_vector = np.array([all_features[name] for name in feature_names])
        
        return feature_vector
    
    # Helper methods
    def _salary_overlap(self, profile: Dict, vacancy: Dict) -> float:
        """Вычисление overlap зарплатных ожиданий."""
        u_from = profile.get('salary_from', 0)
        u_to = profile.get('salary_to', 10_000_000)
        v_from = vacancy.get('salary_from', 0)
        v_to = vacancy.get('salary_to', 10_000_000)
        
        overlap = max(0, min(u_to, v_to) - max(u_from, v_from))
        user_range = max(1, u_to - u_from)
        
        return min(1.0, overlap / user_range)
    
    def _salary_above(self, profile: Dict, vacancy: Dict) -> float:
        """Зарплата выше ожиданий."""
        v_from = vacancy.get('salary_from')
        u_to = profile.get('salary_to')
        
        if v_from and u_to:
            return 1.0 if v_from > u_to else 0.0
        return 0.0
    
    def _location_match(self, profile: Dict, vacancy: Dict) -> float:
        """Точное совпадение локации."""
        pref_locs = [loc.lower() for loc in profile.get('preferred_locations', [])]
        vac_loc = (vacancy.get('location') or '').lower()
        
        if not vac_loc or not pref_locs:
            return 0.5
        
        for loc in pref_locs:
            if loc in vac_loc or vac_loc in loc:
                return 1.0
        
        return 0.0
    
    def _is_remote(self, vacancy: Dict) -> float:
        """Удаленная работа."""
        vac_loc = (vacancy.get('location') or '').lower()
        remote_keywords = ['remote', 'удалённ', 'удален', 'дистанц']
        
        return 1.0 if any(kw in vac_loc for kw in remote_keywords) else 0.0
    
    def _seniority_match(self, profile: Dict, vacancy: Dict) -> float:
        """Точное совпадение уровня."""
        u_sen = (profile.get('seniority') or '').lower()
        v_sen = (vacancy.get('seniority') or '').lower()
        
        if not u_sen or not v_sen:
            return 0.5
        
        return 1.0 if u_sen == v_sen else 0.0
    
    def _seniority_diff(self, profile: Dict, vacancy: Dict) -> float:
        """Разница в уровнях."""
        levels = ['intern', 'junior', 'middle', 'senior', 'lead']
        
        u_sen = (profile.get('seniority') or '').lower()
        v_sen = (vacancy.get('seniority') or '').lower()
        
        try:
            u_idx = levels.index(u_sen)
            v_idx = levels.index(v_sen)
            return abs(u_idx - v_idx) / len(levels)
        except ValueError:
            return 0.5
    
    def _vacancy_age(self, vacancy: Dict) -> float:
        """Возраст вакансии в днях."""
        from datetime import datetime
        
        published = vacancy.get('published_at')
        if not published:
            return 0.0
        
        if isinstance(published, str):
            published = datetime.fromisoformat(published.replace('Z', '+00:00'))
        
        age = (datetime.utcnow() - published).days
        return min(age, 90)  # Cap at 90 days
```

---

## 9. Пример кода: LightGBM Ranker

```python
# services/ml-service/app/ranking/lightgbm_ranker.py

import lightgbm as lgb
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class LightGBMRanker:
    """LightGBM модель для ранжирования вакансий."""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_names = None
        
        if model_path:
            self.load_model(model_path)
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: List[int],
        params: Dict = None
    ) -> Dict:
        """
        Обучение модели.
        
        Args:
            X: Матрица признаков (n_samples, n_features)
            y: Целевая переменная (relevance scores)
            groups: Размеры групп для каждого пользователя
            params: Гиперпараметры модели
        
        Returns:
            Словарь с метриками обучения
        """
        
        if params is None:
            params = {
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [5, 10, 20],
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'num_threads': 4,
            }
        
        # Создание dataset для LightGBM
        train_data = lgb.Dataset(
            X, 
            label=y, 
            group=groups,
            free_raw_data=False
        )
        
        # Обучение модели
        logger.