import { useProtectedMedia } from "../../hooks/useProtectedMedia";

export function ProtectedThumbnail({
  path,
  alt,
  className,
}: {
  path: string;
  alt: string;
  className: string;
}) {
  const url = useProtectedMedia(path);
  return url ? (
    <img src={url} alt={alt} className={className} />
  ) : (
    <div className={className} role="img" aria-label={alt} />
  );
}
