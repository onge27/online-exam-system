// ── Flash message auto-dismiss ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash-msg');
  flashes.forEach((el, i) => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateX(20px)';
      el.style.transition = 'all 0.4s ease';
      setTimeout(() => el.remove(), 400);
    }, 4000 + i * 500);
  });

  // Mobile sidebar toggle
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // Confirm delete actions
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Animate stat cards with delay
  document.querySelectorAll('.stat-card').forEach((el, i) => {
    el.style.animationDelay = `${i * 0.07}s`;
  });
});

// ── Exam Timer ────────────────────────────────────────────────────────────────
function startExamTimer(totalSeconds) {
  const display = document.getElementById('timer-display');
  const form = document.getElementById('exam-form');
  if (!display || !form) return;

  let remaining = totalSeconds;

  function update() {
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    display.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

    display.className = 'timer-display';
    if (remaining <= 60)       display.classList.add('danger');
    else if (remaining <= 300) display.classList.add('warning');

    if (remaining <= 0) {
      clearInterval(interval);
      display.textContent = '00:00';
      alert('⏰ Time is up! Your exam will be submitted now.');
      form.submit();
      return;
    }
    remaining--;
  }

  update();
  const interval = setInterval(update, 1000);
}

// ── Question type toggle (teacher form) ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const typeSelect = document.getElementById('question-type');
  if (!typeSelect) return;

  function toggleSections(val) {
    document.querySelectorAll('.q-section').forEach(s => s.style.display = 'none');
    const target = document.getElementById(`section-${val}`);
    if (target) target.style.display = 'block';
  }

  typeSelect.addEventListener('change', () => toggleSections(typeSelect.value));
  toggleSections(typeSelect.value);
});

// ── Progress bar animate on result page ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.progress-fill').forEach(bar => {
    const target = bar.dataset.width || '0';
    setTimeout(() => bar.style.width = target + '%', 100);
  });
});
