const THEMES = [
    { name: 'Professional Blue', colors: { '--color-primary': '#3b82f6', '--color-secondary': '#60a5fa', '--color-background': '#f3f4f6', '--color-text': '#374151', '--color-card-bg': '#ffffff', '--color-card-border': '#e5e7eb', '--color-input-bg': '#f9fafb', '--color-input-border': '#d1d5db', '--color-input-text': '#111827', '--color-heading': '#1f2937'}},
    { name: 'Emerald Green', colors: { '--color-primary': '#10b981', '--color-secondary': '#34d399', '--color-background': '#ecfdf5', '--color-text': '#064e3b', '--color-card-bg': '#ffffff', '--color-card-border': '#a7f3d0', '--color-input-bg': '#d1fae5', '--color-input-border': '#6ee7b7', '--color-input-text': '#064e3b', '--color-heading': '#065f46'}},
    { name: 'Deep Violet', colors: { '--color-primary': '#8b5cf6', '--color-secondary': '#a78bfa', '--color-background': '#f5f3ff', '--color-text': '#4c1d95', '--color-card-bg': '#ffffff', '--color-card-border': '#ddd6fe', '--color-input-bg': '#ede9fe', '--color-input-border': '#c4b5fd', '--color-input-text': '#4c1d95', '--color-heading': '#5b21b6'}},
    { name: 'Monochrome Slate', colors: { '--color-primary': '#475569', '--color-secondary': '#64748b', '--color-background': '#1e293b', '--color-text': '#e2e8f0', '--color-card-bg': '#334155', '--color-card-border': '#475569', '--color-input-bg': '#475569', '--color-input-border': '#64748b', '--color-input-text': '#f1f5f9', '--color-heading': '#f8fafc'}},
    { name: 'Warm Orange', colors: { '--color-primary': '#f97316', '--color-secondary': '#fb923c', '--color-background': '#fff7ed', '--color-text': '#7c2d12', '--color-card-bg': '#ffffff', '--color-card-border': '#fed7aa', '--color-input-bg': '#ffedd5', '--color-input-border': '#fdba74', '--color-input-text': '#7c2d12', '--color-heading': '#9a3412'}},
    { name: 'Oceanic Teal', colors: { '--color-primary': '#0d9488', '--color-secondary': '#2dd4bf', '--color-background': '#f0fdfa', '--color-text': '#134e4a', '--color-card-bg': '#ccfbf1', '--color-card-border': '#99f6e4', '--color-input-bg': '#f0fdfa', '--color-input-border': '#5eead4', '--color-input-text': '#134e4a', '--color-heading': '#115e59'}},
    { name: 'Sunset Coral', colors: { '--color-primary': '#ff7f50', '--color-secondary': '#ff9b71', '--color-background': '#fff0e6', '--color-text': '#8B4513', '--color-card-bg': '#ffffff', '--color-card-border': '#ffd4b2', '--color-input-bg': '#ffe5d9', '--color-input-border': '#ffc0a1', '--color-input-text': '#8B4513', '--color-heading': '#d2691e'}},
    { name: 'Crimson Red', colors: { '--color-primary': '#dc2626', '--color-secondary': '#ef4444', '--color-background': '#fef2f2', '--color-text': '#991b1b', '--color-card-bg': '#fee2e2', '--color-card-border': '#fecaca', '--color-input-bg': '#fef2f2', '--color-input-border': '#fca5a5', '--color-input-text': '#991b1b', '--color-heading': '#b91c1c'}}
];

let activeTheme = THEMES[0];
let formData = { passport: null, face: null, full_body: null };
let experienceCount = 0;
const dom = {}; // Object to hold all DOM element references for easier access

/**
 * Applies the selected theme by updating CSS variables.
 * @param {object} theme - The theme object containing name and color variables.
 */
const applyTheme = (theme) => {
    activeTheme = theme;
    Object.entries(theme.colors).forEach(([key, value]) => document.documentElement.style.setProperty(key, value));
    localStorage.setItem('selectedTheme', theme.name);
    updateThemeSwitcher();
};

/**
 * Updates the theme switcher UI with the current active theme.
 */
const updateThemeSwitcher = () => {
    let isOpen = false;
    const container = dom.themeSwitcherContainer;
    container.innerHTML = '';

    const button = document.createElement('button');
    button.className = "flex items-center gap-2 px-4 py-2 bg-[var(--color-card-bg)] border border-[var(--color-card-border)] rounded-lg text-[var(--color-text)] hover:bg-gray-500/10 transition-colors";
    button.innerHTML = `<div class="w-4 h-4 rounded-full" style="background-color: ${activeTheme.colors['--color-primary']};"></div>
                        <span>${activeTheme.name}</span>
                        <svg class="w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}" id="theme-chevron" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>`;
    
    const dropdown = document.createElement('div');
    dropdown.className = "hidden absolute right-0 mt-2 w-56 bg-[var(--color-card-bg)] border border-[var(--color-card-border)] rounded-lg shadow-xl z-20 overflow-hidden";
    dropdown.innerHTML = `<ul class="py-1">${THEMES.map(theme => `<li><button data-theme-name="${theme.name}" class="theme-option-btn w-full text-left px-4 py-2 flex items-center gap-3 text-[var(--color-text)] hover:bg-gray-500/10 transition-colors"><div class="w-4 h-4 rounded-full" style="background-color: ${theme.colors['--color-primary']};"></div><span>${theme.name}</span></button></li>`).join('')}</ul>`;
    
    container.append(button, dropdown);
    
    const toggleDropdown = (e) => {
        e.stopPropagation();
        isOpen = !isOpen;
        dropdown.classList.toggle('hidden', !isOpen);
        button.querySelector('#theme-chevron').classList.toggle('rotate-180', isOpen);
    };

    button.addEventListener('click', toggleDropdown);
    document.addEventListener('click', () => {
        if (isOpen) {
            isOpen = false;
            dropdown.classList.add('hidden');
            button.querySelector('#theme-chevron').classList.remove('rotate-180');
        }
    });

    container.querySelectorAll('.theme-option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const themeName = btn.getAttribute('data-theme-name');
            const newTheme = THEMES.find(t => t.name === themeName);
            if (newTheme) applyTheme(newTheme);
        });
    });
};

/**
 * Creates a file input element with a custom preview area.
 * @param {string} name - The name attribute for the file input.
 * @param {string} label - The label text for the file input.
 * @returns {HTMLElement} The container element for the file input.
 */
const createFileInput = (name, label) => {
    const id = `file-input-${name}`;
    const container = document.createElement('div');
    container.className = 'w-full';
    container.innerHTML = `
        <label for="${id}" class="block text-sm font-medium text-center text-[var(--color-text)] mb-2">${label}</label>
        <label for="${id}" id="preview-label-${name}" class="relative w-full aspect-[3/4] flex justify-center items-center px-6 pt-5 pb-6 border-2 border-[var(--color-input-border)] border-dashed rounded-md bg-[var(--color-input-bg)] hover:border-[var(--color-primary)] transition-colors duration-300 cursor-pointer overflow-hidden group">
            <div id="placeholder-${name}" class="space-y-1 text-center transition-opacity duration-300 group-hover:opacity-60">
                <svg class="mx-auto h-12 w-12 text-[var(--color-text)] opacity-40" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>
                <p class="text-xs text-[var(--color-text)] opacity-70">Click to upload</p>
            </div>
            <div id="preview-${name}" class="absolute inset-0 file-input-preview opacity-0 transition-opacity duration-300"></div>
             <div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span class="text-white text-sm font-semibold">Change</span>
            </div>
        </label>
        <input id="${id}" name="${name}" type="file" class="sr-only" accept="image/*">
    `;
    const fileInput = container.querySelector(`#${id}`);
    fileInput.addEventListener('change', handleFileChange);

    const previewDiv = container.querySelector(`#preview-${name}`);
    // Adjust background position for different image types
    if (name === 'passport') {
        previewDiv.style.backgroundSize = '180%';
        previewDiv.style.backgroundPosition = 'left bottom';
    } else if (name === 'full_body') {
        previewDiv.style.backgroundPosition = 'top';
    } else { // 'face'
        previewDiv.style.backgroundPosition = 'center';
    }

    return container;
};

/**
 * Validates the form by checking if all required image inputs have files.
 * Enables/disables the submit button accordingly.
 */
const validateForm = () => {
    dom.submitBtn.disabled = !(formData.passport && formData.face && formData.full_body);
};

/**
 * Handles changes to file input elements, updating the preview and form data.
 * @param {Event} e - The change event object.
 */
const handleFileChange = (e) => {
    const { name, files } = e.target;
    const file = files[0];
    
    const preview = document.getElementById(`preview-${name}`);
    const placeholder = document.getElementById(`placeholder-${name}`);

    if (file && preview && placeholder) {
        formData[name] = file;
        const reader = new FileReader();
        reader.onload = (event) => {
            preview.style.backgroundImage = `url('${event.target.result}')`;
            preview.classList.add('opacity-100');
            placeholder.classList.add('opacity-0');
        };
        reader.readAsDataURL(file);
    } else {
        formData[name] = null;
        if(preview && placeholder) {
            preview.style.backgroundImage = 'none';
            preview.classList.remove('opacity-100');
            placeholder.classList.remove('opacity-0');
        }
    }
    validateForm();
};

/**
 * Adds a new experience field to the form, up to a maximum of 3.
 */
const addExperience = () => {
    if (experienceCount >= 3) {
        return; // Do not add more than 3 experiences
    }
    experienceCount++;
    // Show the experience content section if it's hidden
    dom.experienceContent.classList.remove('hidden');

    const id = `exp-${experienceCount}`;
    const container = document.createElement('div');
    container.id = id;
    container.className = 'grid grid-cols-12 gap-2 items-center animate-fade-in';
    container.innerHTML = `
        <div class="col-span-6">
             <input type="text" name="country" placeholder="Country" class="w-full px-3 py-2 text-sm input-style border rounded-md" required>
        </div>
        <div class="col-span-5">
             <input type="number" name="period" placeholder="Years" class="w-full px-3 py-2 text-sm input-style border rounded-md" required>
        </div>
        <div class="col-span-1">
            <button type="button" data-remove-id="${id}" class="remove-experience-btn p-1 text-gray-400 hover:text-red-500 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" /></svg>
            </button>
        </div>
    `;
    dom.experienceContainer.appendChild(container);
    container.querySelector('.remove-experience-btn').addEventListener('click', (e) => {
        const targetId = e.currentTarget.getAttribute('data-remove-id');
        document.getElementById(targetId)?.remove();
        experienceCount--; // Decrement the count
        // Hide the experience content if no experiences are left
        if (dom.experienceContainer.children.length === 0) {
            dom.experienceContent.classList.add('hidden');
        }
        // Show the add button again if we are below the limit
        if (experienceCount < 3) {
            dom.addExperienceBtn.classList.remove('hidden');
        }
    });

    // Hide the add button if we have reached the limit
    if (experienceCount >= 3) {
        dom.addExperienceBtn.classList.add('hidden');
    }
};

/**
 * Handles the form submission, sends data to the backend, and updates the UI based on the response.
 * @param {Event} e - The submit event object.
 */
const handleSubmit = async (e) => {
    e.preventDefault();
    // Show loading indicator and hide form actions/errors
    dom.formActions.classList.add('hidden');
    dom.generatingIndicator.classList.remove('hidden');
    dom.errorContainer.classList.add('hidden');

    try {
        const payload = new FormData();
        
        // Append image files to the form data
        if (formData.passport) payload.append('passport', formData.passport);
        if (formData.face) payload.append('face', formData.face);
        if (formData.full_body) payload.append('full_body', formData.full_body);

        // Append text fields from the form
        payload.append('contactPhone', dom.cvForm.contactPhone.value);
        payload.append('religion', dom.cvForm.religion.value);

        // Collect, stringify, and append experiences data
        const experiences = Array.from(dom.experienceContainer.children).map(row => ({
            country: row.querySelector('input[name="country"]').value,
            period: row.querySelector('input[name="period"]').value
        })).filter(exp => exp.country && exp.period);
        payload.append('experiences', JSON.stringify(experiences));

        const response = await fetch('/generate', {
            method: 'POST',
            body: payload
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: `HTTP error! Status: ${response.status}` }));
            throw new Error(errorData.message || 'An unknown backend error occurred.');
        }

        const result = await response.json();

        // Populate the result page with generated PDF and full name
        populateResultPage(result.fullName, result.downloadUrl);
        
        // Transition to result section
        dom.formSection.classList.add('hidden');
        dom.resultSection.classList.remove('hidden');
        window.scrollTo(0, 0); // Scroll to top of the page

    } catch (error) {
        dom.errorContainer.classList.remove('hidden');
        dom.errorMessage.textContent = error.message;
    } finally {
        // Hide loading indicator and show form actions again
        dom.formActions.classList.remove('hidden');
        dom.generatingIndicator.classList.add('hidden');
    }
};

/**
 * Populates the result page with the generated CV preview and download link.
 * @param {string} fullName - The full name of the candidate.
 * @param {string} downloadUrl - The URL to download the generated PDF.
 */
const populateResultPage = (fullName, downloadUrl) => {
    const iframe = document.getElementById('pdf-preview-iframe');
    iframe.src = downloadUrl;

    if (fullName && downloadUrl) {
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.href = downloadUrl;
        downloadBtn.download = `${fullName.replace(/ /g, '_')}_CV.pdf`;
        downloadBtn.classList.remove('hidden');
    }
};

/**
 * Resets the application form and state to allow generating a new CV.
 */
const resetApp = () => {
    formData = { passport: null, face: null, full_body: null };
    experienceCount = 0;
    
    document.getElementById('cvForm').reset();
    dom.experienceContainer.innerHTML = '';

    // Reset file input previews
    document.querySelectorAll('input[type="file"]').forEach(input => {
        handleFileChange({ target: input });
    });
    
    // Hide result section and show form section
    dom.resultSection.classList.add('hidden');
    dom.formSection.classList.remove('hidden');
    dom.errorContainer.classList.add('hidden');
    
    validateForm();
};

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Assign DOM elements to the 'dom' object for easy access
    Object.assign(dom, {
        formSection: document.getElementById('form-section'),
        resultSection: document.getElementById('result-section'),
        cvForm: document.getElementById('cvForm'),
        submitBtn: document.getElementById('submit-btn'),
        restartBtn: document.getElementById('restart-btn'),
        backBtn: document.getElementById('back-btn'),
        addExperienceBtn: document.getElementById('add-experience-btn'),
        experienceContainer: document.getElementById('experience-fields-container'),
        experienceFieldset: document.getElementById('experience-fieldset'),
        experienceContent: document.getElementById('experience-content'),
        themeSwitcherContainer: document.getElementById('theme-switcher-container'),
        errorContainer: document.getElementById('error-container'),
        errorMessage: document.getElementById('error-message'),
        generatingIndicator: document.getElementById('generating-indicator'),
        formActions: document.getElementById('form-actions'),
        result: {
            summary: document.getElementById('result-summary'),
            passportImage: document.getElementById('result-passportImage'),
            faceImage: document.getElementById('result-faceImage'),
            full_bodyImage: document.getElementById('result-full_bodyImage'),
        }
    });

    // Append file input components to their respective containers
    document.getElementById('passport-container').appendChild(createFileInput('passport', 'Passport Photo *'));
    document.getElementById('face-container').appendChild(createFileInput('face', 'Face Photo *'));
    document.getElementById('full_body-container').appendChild(createFileInput('full_body', 'Full Body Photo *'));
    
    // Load theme from localStorage on initialization, or apply default
    const savedThemeName = localStorage.getItem('selectedTheme');
    let initialTheme = THEMES[0]; // Default theme
    if (savedThemeName) {
        const foundTheme = THEMES.find(t => t.name === savedThemeName);
        if (foundTheme) {
            initialTheme = foundTheme;
        }
    }
    applyTheme(initialTheme);

    // Add event listeners
    dom.cvForm.addEventListener('submit', handleSubmit);
    dom.restartBtn.addEventListener('click', resetApp);
    dom.backBtn.addEventListener('click', () => {
        dom.resultSection.classList.add('hidden');
        dom.formSection.classList.remove('hidden');
    });
    dom.addExperienceBtn.addEventListener('click', addExperience);

    // Initial form validation check
    validateForm();
});