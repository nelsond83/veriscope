const routes = [
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue'),
    name: 'login',
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('pages/DashboardPage.vue'), name: 'dashboard' },
      { path: 'identities', component: () => import('pages/IdentitiesPage.vue'), name: 'identities' },
      { path: 'identities/:id', component: () => import('pages/IdentityDetailPage.vue'), name: 'identity-detail' },
      { path: 'upload', component: () => import('pages/UploadPage.vue'), name: 'upload' },
      { path: 'reports/:id', component: () => import('pages/ReportDetailPage.vue'), name: 'report-detail' },
      { path: 'unmatched', component: () => import('pages/UnmatchedPage.vue'), name: 'unmatched' },
      { path: 'corrections', component: () => import('pages/CorrectionsPage.vue'), name: 'corrections' },
    ],
  },
  { path: '/:catchAll(.*)*', component: () => import('pages/ErrorNotFound.vue') },
]

export default routes
