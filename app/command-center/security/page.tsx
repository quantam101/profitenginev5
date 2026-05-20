import { StatusPage } from '../StatusPage';
import { commandCenterStatus } from '../statusData';

export default function Page() {
  return <StatusPage {...commandCenterStatus.security} />;
}