from locust import HttpUser, between, task

EMAIL = 'loadtest@example.com'
PASSWORD = 'LoadTest123!'
FULL_NAME = 'Load Test'


class CareerNavigatorUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = None
        self.headers = {}
        self._ensure_user_exists()
        self._login()

    def _ensure_user_exists(self):
        with self.client.post(
            '/api/auth/register',
            json={'email': EMAIL, 'password': PASSWORD, 'full_name': FULL_NAME},
            name='POST /api/auth/register (setup)',
            catch_response=True,
        ) as response:
            if response.status_code in (201, 409):
                response.success()
            else:
                response.failure(f'Unexpected registration status: {response.status_code}')

    def _login(self):
        with self.client.post(
            '/api/auth/login',
            json={'email': EMAIL, 'password': PASSWORD},
            name='POST /api/auth/login',
            catch_response=True,
        ) as response:
            if response.ok:
                self.token = response.json().get('access_token')
                self.headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
                response.success()
            else:
                response.failure(f'Login failed: {response.status_code}')

    @task(8)
    def health(self):
        self.client.get('/health', name='GET /health')

    @task(6)
    def list_vacancies(self):
        self.client.get(
            '/api/vacancies',
            params={'page': 1, 'page_size': 20, 'status': 'active'},
            name='GET /api/vacancies',
        )

    @task(4)
    def auth_me(self):
        self.client.get('/api/auth/me', headers=self.headers, name='GET /api/auth/me')

    @task(4)
    def profile_me(self):
        self.client.get('/api/profiles/me', headers=self.headers, name='GET /api/profiles/me')

    @task(2)
    def recommendations_cached(self):
        self.client.get(
            '/api/recommendations/me',
            headers=self.headers,
            name='GET /api/recommendations/me',
            catch_response=True,
        )

    @task(1)
    def recommendations_refresh(self):
        self.client.post(
            '/api/recommendations/refresh',
            headers=self.headers,
            name='POST /api/recommendations/refresh',
            catch_response=True,
        )
