import { useLocalSearchParams } from 'expo-router';

import { WorkScreen } from '@/features/jobs/presentation/screens/WorkScreen';

export default function WorkRoute() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return <WorkScreen jobId={id ?? ''} />;
}
