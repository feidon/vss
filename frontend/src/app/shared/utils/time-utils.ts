const pad = (n: number): string => String(n).padStart(2, '0');

export function localDatetimeToEpoch(localStr: string): number {
  return Math.floor(new Date(localStr).getTime() / 1000);
}

export function epochToLocalDatetime(epoch: number): string {
  const dt = new Date(epoch * 1000);
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
}

export function epochToDisplayTime(epoch: number): string {
  if (!epoch) {
    return '\u2014';
  }
  const dt = new Date(epoch * 1000);
  return `${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
}
