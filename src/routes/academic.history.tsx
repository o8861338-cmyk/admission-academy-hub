import { createFileRoute } from '@tanstack/react-router';
import { SessionHistory } from '@/modules/academic/pages/SessionHistory';
import { academicHead, academicSearch } from '@/modules/academic/seo';
export const Route = createFileRoute('/academic/history')({ head: academicHead('Session History', 'Manage trainer session history in the academic portal.'), validateSearch: academicSearch, component: SessionHistory });
