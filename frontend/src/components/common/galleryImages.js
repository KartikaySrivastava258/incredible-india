const modules = import.meta.glob('../../assets/kalaa-gallery/*.jpg', {
  eager: true,
  import: 'default',
});

export const GALLERY_IMAGES = Object.keys(modules)
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
  .map((key) => modules[key])
  .filter(Boolean);
