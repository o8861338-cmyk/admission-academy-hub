import { createFileRoute } from '@tanstack/react-router';
import { MyClassSchedule } from '@/modules/academic/pages/MyClassSchedule';
import { academicHead, academicSearch } from '@/modules/academic/seo';
export const Route = createFileRoute('/academic/schedule')({ head: academicHead('Schedule', 'Manage trainer schedule in the academic portal.'), validateSearch: academicSearch, component: MyClassSchedule });
