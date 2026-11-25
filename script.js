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

  // Curated field portfolio: reveal four records per click, never all at once.
  const galleryCards = [...document.querySelectorAll('[data-gallery-card]')];
  const galleryToggle = document.querySelector('#gallery-toggle');
  if (galleryToggle && galleryCards.length) {
    let visibleCount = 4;
    const renderGallery = () => {
      galleryCards.forEach((card, index) => {
        const show = index < visibleCount;
        card.hidden = !show;
        if (show) card.classList.add('is-visible');
      });
      galleryToggle.hidden = visibleCount >= galleryCards.length;
      galleryToggle.setAttribute('aria-expanded', String(visibleCount > 4));
      const label = galleryToggle.querySelector('span:first-child');
      if (label) label.textContent = '4개 더보기';
      const counter = galleryToggle.querySelector('small');
      if (counter) counter.textContent = Math.min(visibleCount, galleryCards.length) + ' / ' + galleryCards.length;
    };
    galleryToggle.addEventListener('click', () => {
      visibleCount = Math.min(visibleCount + 4, galleryCards.length);
      renderGallery();
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
  const photoVideo = document.querySelector('#photo-dialog-video');
  const mediaItems = post => Array.isArray(post?.media) && post.media.length ? post.media : (post?.images || []).map(src => ({type:'image',src}));
  function stopVideo() { if (photoVideo) { photoVideo.pause(); photoVideo.hidden=true; photoVideo.removeAttribute('src'); photoVideo.load(); } }
  const photoError = document.querySelector('#photo-dialog-error');
  const photoPrev = document.querySelector('#photo-prev');
  const photoNext = document.querySelector('#photo-next');
  const photoCount = document.querySelector('#photo-count');
  const photoThumbnails = document.querySelector('#photo-thumbnails');
  const photoNote = document.querySelector('#photo-collection-note');
  let currentPost = null;
  let currentPhotoIndex = 0;
  let lastPhotoTrigger = null;
  let previousBodyOverflow = '';
  let photoRetry = false;

  function renderPhoto() {
    if (!currentPost || !photoDialog) return;
    const images = mediaItems(currentPost);
    if (!images.length) return;
    currentPhotoIndex = (currentPhotoIndex + images.length) % images.length;
    photoRetry = false;
    photoError.hidden = true;
    stopVideo();
    const item = images[currentPhotoIndex];
    photoImage.hidden = item.type === 'video';
    if (item.type === 'video' && photoVideo) {
      photoImage.removeAttribute('src');
      photoVideo.poster = item.poster || ''; photoVideo.src = item.src; photoVideo.hidden = false;
    } else {
      photoImage.alt = currentPost.title + ' - ' + (currentPhotoIndex + 1) + '번째 사진';
      photoImage.src = item.src + '?v=3';
    }
    photoCount.textContent = (currentPhotoIndex + 1) + ' / ' + images.length;
    photoPrev.hidden = images.length < 2;
    photoNext.hidden = images.length < 2;
    photoThumbnails?.querySelectorAll('button').forEach((button, i) => {
      button.setAttribute('aria-pressed', String(i === currentPhotoIndex));
      button.classList.toggle('is-active', i === currentPhotoIndex);
    });
    const selected = photoThumbnails?.children[currentPhotoIndex];
    if (selected) {
      const left = selected.offsetLeft - photoThumbnails.offsetLeft;
      if (left < photoThumbnails.scrollLeft) photoThumbnails.scrollLeft = left;
      else if (left + selected.offsetWidth > photoThumbnails.scrollLeft + photoThumbnails.clientWidth) photoThumbnails.scrollLeft = left + selected.offsetWidth - photoThumbnails.clientWidth;
    }
  }

  function openPhoto(postId, trigger) {
    const post = photoPosts.get(postId);
    if (!post || !photoDialog) return;
    currentPost = post;
    currentPhotoIndex = 0;
    if (photoThumbnails) {
      photoThumbnails.replaceChildren();
      const items = mediaItems(post);
      photoThumbnails.hidden = items.length < 2;
      if (items.length > 1) items.forEach((item, i) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.setAttribute('aria-label', (i + 1) + '번째 ' + (item.type === 'video' ? '영상' : '사진') + ' 보기');
        const img = document.createElement('img');
        img.src = (item.poster || item.src) + '?v=20261125'; img.alt = ''; img.loading = 'lazy';
        button.append(img);
        if (item.type === 'video') { const mark=document.createElement('span'); mark.className='video-thumb-mark'; mark.textContent='▶'; button.append(mark); }
        button.addEventListener('click', () => { currentPhotoIndex = i; renderPhoto(); });
        photoThumbnails.append(button);
      });
      photoThumbnails.scrollLeft = 0;
    }
    if (photoNote) {
      const items = mediaItems(post);
      const videos = items.filter(m=>m.type==='video').length;
      const pending = post.media_checked === false && post.media_total > items.length;
      const missing = post.media_unavailable || (post.video_count && !post.media ? post.video_count : 0);
      const text = pending ? '현재 ' + items.length + '개 · 원본 추가 자료 확인 중' : missing ? '일부 영상은 아직 재생 파일을 확보하지 못했습니다. 원문에서 확인해 주세요.' : videos ? '사진 ' + (items.length-videos) + '장 · 영상 ' + videos + '개' : '';
      photoNote.textContent = text;
      photoNote.hidden = !text;
    }
    lastPhotoTrigger = trigger || null;
    document.querySelector('#photo-dialog-title').textContent = post.title;
    document.querySelector('#photo-dialog-meta').textContent = post.date + ' · ' + post.category;
    document.querySelector('#photo-dialog-summary').textContent = post.summary;
    const sourceLink = document.querySelector('#photo-dialog-source');
    if (sourceLink) {
      sourceLink.hidden = !/^https:\/\/www\.instagram\.com\/p\/[A-Za-z0-9_-]+\/$/.test(post.source || '');
      if (!sourceLink.hidden) sourceLink.href = post.source;
    }
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
    stopVideo();
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
    stopVideo();
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
    if (!photoDialog?.open || !currentPost || event.target === photoVideo) return;
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
    if (!currentPost || photoImage.hidden) return;
    if (!photoRetry) {
      photoRetry = true;
      photoImage.src = mediaItems(currentPost)[currentPhotoIndex].src + '?v=3&retry=1';
    } else {
      photoImage.hidden = true;
      photoError.hidden = false;
    }
  });

  photoVideo?.addEventListener('error', () => { if (currentPost && !photoVideo.hidden && photoVideo.getAttribute('src')) photoError.hidden=false; });

  // Mobile: swipe horizontally between photos, with vertically scrollable descriptions.
  let touchStart = null;
  photoImage?.addEventListener('touchstart', (event) => {
    const touch = event.changedTouches[0];
    touchStart = { x: touch.clientX, y: touch.clientY };
  }, { passive: true });
  photoImage?.addEventListener('touchend', (event) => {
    if (!touchStart || !currentPost || mediaItems(currentPost).length < 2) return;
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
