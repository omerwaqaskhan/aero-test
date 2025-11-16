/**
 * Generate a URL-friendly slug from a string
 */
export function createSlug(text) {
  if (!text) return '';
  
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')           // Replace spaces with hyphens
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars except hyphens
    .replace(/\-\-+/g, '-')         // Replace multiple hyphens with single hyphen
    .replace(/^-+/, '')             // Trim hyphens from start
    .replace(/-+$/, '');             // Trim hyphens from end
}

/**
 * Extract hotel ID from slug or return slug as-is
 * This handles both old ID-based URLs and new slug-based URLs
 */
export function parseHotelIdentifier(identifier) {
  // If it's a UUID format, return as-is
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (uuidRegex.test(identifier)) {
    return identifier;
  }
  // Otherwise, it's a slug
  return identifier;
}

