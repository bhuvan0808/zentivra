export interface ValidationError {
  field: string;
  message: string;
}

function isValidUrl(value: string): boolean {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

export function validateSourceForm(data: {
  display_name: string;
  url: string;
}): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!data.display_name.trim()) {
    errors.push({ field: "display_name", message: "Source name is required." });
  } else if (data.display_name.length > 255) {
    errors.push({ field: "display_name", message: "Source name must be 255 characters or fewer." });
  }

  if (!data.url.trim()) {
    errors.push({ field: "url", message: "URL is required." });
  } else if (!isValidUrl(data.url)) {
    errors.push({ field: "url", message: "Please enter a valid URL (e.g. https://example.com)." });
  }

  return errors;
}

export function toSlug(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}
