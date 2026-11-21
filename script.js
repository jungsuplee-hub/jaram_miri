(() => {
  const root = document.documentElement;
  root.classList.add('js');

  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#mobile-menu');
  const closeMenu = () => {
    if (!toggle || !menu) return;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', '메뉴 열기');
    menu.hidden = true;
  };
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
      menu.hidden = !open;
    });
    menu.addEventListener('click', (event) => {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
    document.addEventListener('click', (event) => {
      if (!menu.hidden && !menu.contains(event.target) && !toggle.contains(event.target)) closeMenu();
    });
    window.matchMedia('(min-width: 861px)').addEventListener('change', (event) => {
      if (event.matches) closeMenu();
    });
  }

  // Filter only verifiable activity records, without hiding sources.
  const filterButtons = [...document.querySelectorAll('.activity-filter')];
  const records = [...document.querySelectorAll('.activity-card[data-type]')];
  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const filter = button.dataset.filter;
      filterButtons.forEach((candidate) => {
        const selected = candidate === button;
        candidate.classList.toggle('is-active', selected);
        candidate.setAttribute('aria-pressed', String(selected));
      });
      records.forEach((card) => {
        card.hidden = filter !== 'all' && card.dataset.type !== filter;
      });
    });
  });

  // Instagram activity portfolio: four previews, full local gallery, photo viewer.
  const galleryCards = [...document.querySelectorAll('[data-gallery-card]')];
  const galleryToggle = document.querySelector('#gallery-toggle');
  const previewCount = 4;
  if (galleryToggle && galleryCards.length) {
    let expanded = false;
    const renderGallery = () => {
      galleryCards.forEach((card, i) => {
        const show = expanded || i < previewCount;
        card.hidden = !show;
        if (show) card.classList.add('is-visible');
      });
      galleryToggle.setAttribute('aria-expanded', String(expanded));
      galleryToggle.querySelector('span:first-child').textContent = expanded ? '접기' : '전체 활동 보기';
      galleryToggle.querySelector('small').textContent =
        (expanded ? galleryCards.length : Math.min(galleryCards.length, previewCount)) +
        ' / ' + galleryCards.length;
      galleryToggle.querySelector('.gallery-toggle-icon').textContent = expanded ? '↑' : '↓';
      galleryToggle.hidden = galleryCards.length <= previewCount;
    };
    galleryToggle.addEventListener('click', () => {
      expanded = !expanded;
      renderGallery();
      if (!expanded) document.querySelector('.field-intro')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    renderGallery();
  }

  let photoData = [];
  try {
    photoData = JSON.parse(document.querySelector('#photo-gallery-data')?.textContent || '[]');
  } catch (error) {
    console.warn('Gallery data is not available.', error);
  }
  const photoPosts = new Map(photoData.map((post) => [post.id, post]));
  const photoDialog = document.querySelector('#photo-dialog');
  const photoImage = document.querySelector('#photo-dialog-image');
  const photoError = document.querySelector('#photo-dialog-error');
  const photoPrev = document.querySelector('#photo-prev');
  const photoNext = document.querySelector('#photo-next');
  const photoCount = document.querySelector('#photo-count');
  let currentPost = null;
  let currentPhotoIndex = 0;
  let lastPhotoTrigger = null;
  let previousBodyOverflow = '';
  let photoRetry = false;

  function renderPhoto() {
    if (!currentPost || !photoDialog) return;
    const images = currentPost.images || [];
    if (!images.length) return;
    currentPhotoIndex = (currentPhotoIndex + images.length) % images.length;
    photoRetry = false;
    photoError.hidden = true;
    photoImage.hidden = false;
    const url = images[currentPhotoIndex];
    photoImage.alt = currentPost.title + ' - ' + (currentPhotoIndex + 1) + '번째 사진';
    photoImage.src = url + '?v=3';
    photoCount.textContent = (currentPhotoIndex + 1) + ' / ' + images.length;
    photoPrev.hidden = images.length < 2;
    photoNext.hidden = images.length < 2;
  }

  function openPhoto(postId, trigger) {
    const post = photoPosts.get(postId);
    if (!post || !photoDialog) return;
    currentPost = post;
    currentPhotoIndex = 0;
    lastPhotoTrigger = trigger || null;
    document.querySelector('#photo-dialog-title').textContent = post.title;
    document.querySelector('#photo-dialog-meta').textContent = post.date + ' · ' + post.category;
    document.querySelector('#photo-dialog-summary').textContent = post.summary;
    const captionWrap = document.querySelector('#photo-dialog-caption-wrap');
    captionWrap.hidden = !post.caption;
    document.querySelector('#photo-dialog-caption').textContent = post.caption || '';
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    if (typeof photoDialog.showModal === 'function') photoDialog.showModal();
    else photoDialog.setAttribute('open', '');
    renderPhoto();
    document.querySelector('#photo-dialog-close').focus();
  }

  function closePhoto() {
    if (!photoDialog) return;
    if (typeof photoDialog.close === 'function' && photoDialog.open) photoDialog.close();
    else {
      photoDialog.removeAttribute('open');
      document.body.style.overflow = previousBodyOverflow;
      lastPhotoTrigger?.focus();
    }
  }

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-gallery-open]');
    if (trigger) {
      event.preventDefault();
      openPhoto(trigger.dataset.galleryOpen, trigger);
    }
  });
  document.querySelector('#photo-dialog-close')?.addEventListener('click', closePhoto);
  photoDialog?.addEventListener('close', () => {
    document.body.style.overflow = previousBodyOverflow;
    currentPost = null;
    lastPhotoTrigger?.focus();
  });
  photoDialog?.addEventListener('click', (event) => {
    if (event.target === photoDialog) closePhoto();
  });
  photoPrev?.addEventListener('click', () => {
    currentPhotoIndex--;
    renderPhoto();
  });
  photoNext?.addEventListener('click', () => {
    currentPhotoIndex++;
    renderPhoto();
  });
  document.addEventListener('keydown', (event) => {
    if (!photoDialog?.open || !currentPost) return;
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      currentPhotoIndex--;
      renderPhoto();
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      currentPhotoIndex++;
      renderPhoto();
    } else if (event.key === 'Escape') closePhoto();
  });
  photoImage?.addEventListener('error', () => {
    if (!currentPost) return;
    if (!photoRetry) {
      photoRetry = true;
      photoImage.src = currentPost.images[currentPhotoIndex] + '?v=3&retry=1';
    } else {
      photoImage.hidden = true;
      photoError.hidden = false;
    }
  });

  // Mobile: swipe horizontally between photos, with vertically scrollable descriptions.
  let touchStart = null;
  photoImage?.addEventListener('touchstart', (event) => {
    const touch = event.changedTouches[0];
    touchStart = { x: touch.clientX, y: touch.clientY };
  }, { passive: true });
  photoImage?.addEventListener('touchend', (event) => {
    if (!touchStart || !currentPost || currentPost.images.length < 2) return;
    const touch = event.changedTouches[0];
    const dx = touch.clientX - touchStart.x;
    const dy = touch.clientY - touchStart.y;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) {
      currentPhotoIndex += dx > 0 ? -1 : 1;
      renderPhoto();
    }
    touchStart = null;
  }, { passive: true });

  // Protect existing activity photos from occasional stale CDN/error responses.
  document.querySelectorAll('img[src*="assets/instagram/"]').forEach((img) => {
    let didRetry = false;
    img.addEventListener('error', () => {
      if (!didRetry) {
        didRetry = true;
        const cleanSrc = img.getAttribute('src').split('?')[0];
        img.src = cleanSrc + '?v=3&retry=1';
      } else {
        img.hidden = true;
        const parent = img.parentElement;
        let fallback = parent.querySelector('.photo-fallback');
        if (!fallback) {
          fallback = document.createElement('span');
          fallback.className = 'photo-fallback';
          fallback.textContent = '사진을 불러올 수 없습니다.';
          parent.appendChild(fallback);
        }
        fallback.hidden = false;
      }
    });
  });

  const year = document.querySelector('#year');
  if (year) year.textContent = String(new Date().getFullYear());

  const revealElements = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver((entries, obs) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      }
    }, { threshold: 0.09, rootMargin: '0px 0px -25px 0px' });
    revealElements.forEach((element) => observer.observe(element));
  } else {
    revealElements.forEach((element) => element.classList.add('is-visible'));
  }
})();
