const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('pages/DashboardPage.vue'), name: 'dashboard' },
      { path: 'cases', component: () => import('pages/CasesPage.vue'), name: 'cases' },
      { path: 'cases/:id', component: () => import('pages/CaseDetailPage.vue'), name: 'case-detail' },
      { path: 'upload', component: () => import('pages/UploadPage.vue'), name: 'upload' },
      { path: 'reports/:id', component: () => import('pages/ReportDetailPage.vue'), name: 'report-detail' },
    ],
  },
  { path: '/:catchAll(.*)*', component: () => import('pages/ErrorNotFound.vue') },
]

export default routes
