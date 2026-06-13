// ==========================================================================
// ShrinkLab - app.js
// Handles: toggle secret message field, file name display,
// drag & drop on upload area, submit loading state
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {

    /* ---------------------------------------------------------------
       1. Toggle "Pesan Rahasia" field based on selected algoritma
    ----------------------------------------------------------------*/
    const algoritmaSelect = document.querySelector('select[name="algoritma"]');
    const secretGroup = document.querySelector('.module-group.secret-message');

    if (algoritmaSelect && secretGroup) {
        const secretInput = secretGroup.querySelector('input[name="pesan_rahasia"]');

        const toggleSecretField = () => {
            if (algoritmaSelect.value === 'stegano_hide') {
                secretGroup.classList.add('is-visible');
                if (secretInput) secretInput.setAttribute('required', 'required');
            } else {
                secretGroup.classList.remove('is-visible');
                if (secretInput) secretInput.removeAttribute('required');
            }
        };

        toggleSecretField();
        algoritmaSelect.addEventListener('change', toggleSecretField);
    }

    /* ---------------------------------------------------------------
       2. Show selected file name + drag & drop styling
    ----------------------------------------------------------------*/
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.querySelector('input[name="file_input"]');

    if (uploadArea && fileInput) {
        // Create a element to show file name
        let fileNameEl = uploadArea.querySelector('.file-name');
        if (!fileNameEl) {
            fileNameEl = document.createElement('p');
            fileNameEl.className = 'file-name';
            uploadArea.appendChild(fileNameEl);
        }

        const updateFileName = () => {
            if (fileInput.files && fileInput.files.length > 0) {
                fileNameEl.textContent = '📄 ' + fileInput.files[0].name;
            } else {
                fileNameEl.textContent = '';
            }
        };

        fileInput.addEventListener('change', updateFileName);

        // Drag & drop visual feedback + assigning file
        ['dragover', 'dragenter'].forEach(evt => {
            uploadArea.addEventListener(evt, (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'dragend'].forEach(evt => {
            uploadArea.addEventListener(evt, () => {
                uploadArea.classList.remove('dragover');
            });
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                fileInput.files = files;
                updateFileName();
            }
        });
    }

    /* ---------------------------------------------------------------
       3. Loading state on submit button
    ----------------------------------------------------------------*/
    const form = document.querySelector('form');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;

    if (form && submitBtn) {
        form.addEventListener('submit', () => {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            const originalText = submitBtn.textContent;
            submitBtn.dataset.originalText = originalText;
            submitBtn.textContent = ' PROCESSING...';
        });
    }

});
