(() => {
  'use strict';


  // Fill local demo credentials without submitting the form automatically.
  document.querySelectorAll('[data-demo-username][data-demo-password]').forEach((button) => {
    button.addEventListener('click', () => {
      const username = document.getElementById('loginUsername');
      const password = document.getElementById('loginPassword');
      if (!username || !password) return;
      username.value = button.dataset.demoUsername || '';
      password.value = button.dataset.demoPassword || '';
      username.dispatchEvent(new Event('input', { bubbles: true }));
      password.dispatchEvent(new Event('input', { bubbles: true }));
      password.focus();
    });
  });

  // Password visibility toggle on the sign-in screen.
  const passwordToggle = document.getElementById('togglePassword');
  if (passwordToggle) {
    passwordToggle.addEventListener('click', () => {
      const password = document.getElementById('loginPassword');
      if (!password) return;
      const visible = password.type === 'password';
      password.type = visible ? 'text' : 'password';
      passwordToggle.textContent = visible ? 'إخفاء' : 'إظهار';
      passwordToggle.setAttribute('aria-label', visible ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور');
    });
  }

  // Switch the add-item form fields according to the selected item type.
  const itemType = document.getElementById('itemType');
  if (itemType) {
    const syncFields = () => {
      const isProject = itemType.value === 'project';
      document.querySelectorAll('.book-only').forEach((node) => node.classList.toggle('hidden', isProject));
      document.querySelectorAll('.project-only').forEach((node) => node.classList.toggle('hidden', !isProject));
    };
    itemType.addEventListener('change', syncFields);
    syncFields();
  }

  // Ask for confirmation before destructive actions.
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.getAttribute('data-confirm') || 'هل أنت متأكد؟';
      if (!window.confirm(message)) event.preventDefault();
    });
  });

  // Dismiss flash messages without reloading the page.
  document.querySelectorAll('.flash-close').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });
})();
