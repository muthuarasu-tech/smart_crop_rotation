/* ============================================================
   SMART CROP ROTATION - script.js
   Client-side validation, helper UI behaviours
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('recommendForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            if (validateForm(form)) {
                form.submit();
            }
        });
    }

    // Auto-hide flash alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.6s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 600);
        }, 5000);
    });

    initReveal();
    initCounters();
    initNavShadow();
});

/* ---------------- Scroll reveal ---------------- */
function initReveal() {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;
    const io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
}

/* ---------------- Animated counters ---------------- */
function initCounters() {
    const counters = document.querySelectorAll('.count[data-target]');
    if (!counters.length) return;
    const io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            animateCount(entry.target);
            io.unobserve(entry.target);
        });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { io.observe(el); });
}

function animateCount(el) {
    const target = parseFloat(el.getAttribute('data-target'));
    if (isNaN(target)) return;
    const duration = 1000;
    const start = performance.now();
    function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = target;
    }
    requestAnimationFrame(step);
}

/* ---------------- Navbar shadow on scroll ---------------- */
function initNavShadow() {
    const nav = document.querySelector('.navbar');
    window.addEventListener('scroll', function () {
        if (window.scrollY > 10) nav.classList.add('scrolled');
        else nav.classList.remove('scrolled');
    }, { passive: true });
}

function validateForm(form) {
    clearErrors(form);

    const rules = [
        { field: 'previous_crop', test: v => !!v, msg: 'Please select the previous crop.' },
        { field: 'season', test: v => !!v, msg: 'Please select the season.' },
        { field: 'soil_type', test: v => !!v, msg: 'Please select the soil type.' },
        { field: 'ph', test: v => v !== '' && !isNaN(v) && v >= 0 && v <= 14, msg: 'pH must be between 0 and 14.' },
        { field: 'n', test: v => v === '' || (!isNaN(v) && v >= 0), msg: 'Nitrogen must be a non-negative number.' },
        { field: 'p', test: v => v === '' || (!isNaN(v) && v >= 0), msg: 'Phosphorus must be a non-negative number.' },
        { field: 'k', test: v => v === '' || (!isNaN(v) && v >= 0), msg: 'Potassium must be a non-negative number.' },
        { field: 'rainfall', test: v => v === '' || (!isNaN(v) && v >= 0), msg: 'Rainfall must be non-negative.' },
        { field: 'temperature', test: v => v === '' || (!isNaN(v) && v >= 5 && v <= 45), msg: 'Temperature must be between 5 and 45 °C.' },
        { field: 'humidity', test: v => v === '' || (!isNaN(v) && v >= 0 && v <= 100), msg: 'Humidity must be between 0 and 100.' },
        { field: 'water_availability', test: v => !!v, msg: 'Please select water availability.' },
        { field: 'irrigation', test: v => !!v, msg: 'Please select the irrigation type.' },
        { field: 'region', test: v => !!v, msg: 'Please select a region.' },
        { field: 'previous_yield', test: v => v === '' || (!isNaN(v) && v >= 0), msg: 'Yield must be non-negative.' },
        { field: 'disease_level', test: v => !!v, msg: 'Please select disease level.' },
        { field: 'fertilizer_usage', test: v => !!v, msg: 'Please select fertilizer usage.' },
        { field: 'target_season', test: v => !!v, msg: 'Please select the target season.' },
    ];

    let ok = true;
    rules.forEach(function (rule) {
        const input = form.querySelector('[name="' + rule.field + '"]');
        if (!input) return;
        const value = (input.value || '').trim();
        if (!rule.test(value)) {
            showError(input, rule.msg);
            ok = false;
        }
    });

    if (!ok) {
        const firstError = form.querySelector('.field-error');
        if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return ok;
}

function showError(input, message) {
    const wrapper = input.closest('.field');
    if (!wrapper) return;
    input.style.borderColor = '#C62828';
    let el = wrapper.querySelector('.field-error');
    if (!el) {
        el = document.createElement('p');
        el.className = 'error field-error';
        wrapper.appendChild(el);
    }
    el.textContent = message;
}

function clearErrors(form) {
    form.querySelectorAll('.field-error').forEach(el => el.remove());
    form.querySelectorAll('input, select').forEach(el => (el.style.borderColor = ''));
}