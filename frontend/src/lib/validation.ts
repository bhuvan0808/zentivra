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
  name: string;
  url: string;
  feed_url: string;
  rate_limit_rpm: number;
  crawl_depth: number;
  keywords: string[];
}): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!data.name.trim()) {
    errors.push({ field: "name", message: "Name is required." });
  } else if (data.name.length > 100) {
    errors.push({ field: "name", message: "Name must be 100 characters or fewer." });
  }

  if (!data.url.trim()) {
    errors.push({ field: "url", message: "URL is required." });
  } else if (!isValidUrl(data.url)) {
    errors.push({ field: "url", message: "Please enter a valid URL (e.g. https://example.com)." });
  }

  if (data.feed_url.trim() && !isValidUrl(data.feed_url)) {
    errors.push({ field: "feed_url", message: "Please enter a valid feed URL or leave it empty." });
  }

  if (data.rate_limit_rpm < 1 || data.rate_limit_rpm > 60) {
    errors.push({ field: "rate_limit_rpm", message: "Rate limit must be between 1 and 60 requests per minute." });
  }

  if (data.crawl_depth < 1 || data.crawl_depth > 5) {
    errors.push({ field: "crawl_depth", message: "Crawl depth must be between 1 and 5." });
  }

  for (const keyword of data.keywords) {
    if (keyword.length > 50) {
      errors.push({ field: "keywords", message: "Each keyword must be 50 characters or fewer." });
      break;
    }
  }

  return errors;
}
