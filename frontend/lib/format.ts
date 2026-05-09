/** 포맷 유틸리티. */

/** 원화 포맷: 1234567 → "₩1,234,567" */
export function formatKRW(won: number): string {
  return `₩${won.toLocaleString("ko-KR")}`;
}

/** 분 → "7일 14시간" 형태 */
export function formatDuration(minutes: number): string {
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  if (days === 0) return `${hours}시간`;
  if (hours === 0) return `${days}일`;
  return `${days}일 ${hours}시간`;
}

/** 분 → "6시간 42분" 형태 (에지 단위) */
export function formatEdgeDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}분`;
  if (m === 0) return `${h}시간`;
  return `${h}시간 ${m}분`;
}

