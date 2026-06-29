/**
 * FTRA - Upload Manager
 * Manejo de carga de facturas con drag & drop, cámara, progreso
 */

class UploadManager {
    constructor() {
        this.files = [];
        this.uploadInProgress = false;
        this.init();
    }

    init() {
        this.setupDragDrop();
        this.setupFileInput();
        this.setupCameraButton();
        this.setupUploadButton();
        this.setupCancelButton();
    }

    setupDragDrop() {
        const dropZone = document.getElementById('dropZone');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults.bind(this), false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = '#f0f9ff';
                dropZone.style.borderColor = '#0284c7';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = 'transparent';
                dropZone.style.borderColor = '#2563eb';
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        });

        dropZone.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    setupFileInput() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }

        // Vincular botón de seleccionar archivos
        const selectBtn = document.getElementById('selectFilesBtn');
        if (selectBtn) {
            selectBtn.addEventListener('click', () => {
                document.getElementById('fileInput').click();
            });
        }
    }

    setupCameraButton() {
        const cameraBtn = document.getElementById('takeCameraBtn');
        const cameraInput = document.getElementById('cameraInput');

        if (cameraBtn && cameraInput) {
            cameraBtn.addEventListener('click', () => {
                cameraInput.click();
            });

            cameraInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFiles(e.target.files);
                }
            });
        }
    }

    setupUploadButton() {
        // El botón será creado dinámicamente después de seleccionar archivos
        const uploadMoreBtn = document.getElementById('uploadMoreBtn');
        if (uploadMoreBtn) {
            uploadMoreBtn.addEventListener('click', () => {
                this.resetUpload();
            });
        }
    }

    setupCancelButton() {
        const cancelBtn = document.getElementById('cancelUploadBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.cancelUpload();
            });
        }
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFiles(files) {
        const validFiles = [];

        for (let file of files) {
            // Validar tipo
            if (!this.isValidFileType(file)) {
                this.addError(`${file.name}: Tipo de archivo no soportado`);
                continue;
            }

            // Validar tamaño (50 MB)
            if (file.size > 52428800) {
                this.addError(`${file.name}: Tamaño excede 50 MB`);
                continue;
            }

            validFiles.push(file);
        }

        if (validFiles.length > 0) {
            this.files = validFiles;
            this.displayFiles();
            this.showUploadButton();
        }
    }

    isValidFileType(file) {
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];
        const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff'];

        return validTypes.includes(file.type) || 
               validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    displayFiles() {
        const container = document.getElementById('filesContainer');
        const filesList = document.getElementById('filesList');
        const fileCount = document.getElementById('fileCount');

        fileCount.textContent = this.files.length;
        filesList.innerHTML = '';

        this.files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'col-12 col-sm-6';
            fileItem.innerHTML = `
                <div class="card" style="position: relative;">
                    <div class="card-body p-2">
                        <div class="text-center mb-2">
                            <i class="bi bi-file-earmark${this.getIconClass(file)}" style="font-size: 32px; color: #2563eb;"></i>
                        </div>
                        <p class="mb-1 text-truncate small"><strong>${file.name}</strong></p>
                        <small class="text-muted">${this.formatFileSize(file.size)}</small>
                        <button type="button" class="btn-close btn-sm" style="position: absolute; top: 8px; right: 8px;" 
                                onclick="uploadManager.removeFile(${index})"></button>
                    </div>
                </div>
            `;
            filesList.appendChild(fileItem);
        });

        container.classList.remove('d-none');
    }

    getIconClass(file) {
        const name = file.name.toLowerCase();
        if (name.endsWith('.pdf')) return '-pdf';
        if (name.endsWith('.png')) return '-image';
        if (name.match(/\.(jpg|jpeg)$/)) return '-image';
        return '';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    removeFile(index) {
        this.files.splice(index, 1);
        if (this.files.length === 0) {
            document.getElementById('filesContainer').classList.add('d-none');
            this.hideUploadButton();
        } else {
            this.displayFiles();
        }
    }

    showUploadButton() {
        const dropZone = document.getElementById('dropZone');
        let uploadBtn = document.getElementById('uploadFilesBtn');

        if (!uploadBtn) {
            uploadBtn = document.createElement('button');
            uploadBtn.id = 'uploadFilesBtn';
            uploadBtn.type = 'button';
            uploadBtn.className = 'btn btn-success mt-3';
            uploadBtn.innerHTML = '<i class="bi bi-upload me-2"></i>Subir y Procesar';
            uploadBtn.addEventListener('click', () => this.uploadFiles());

            dropZone.parentElement.appendChild(uploadBtn);
        }

        uploadBtn.classList.remove('d-none');
    }

    hideUploadButton() {
        const uploadBtn = document.getElementById('uploadFilesBtn');
        if (uploadBtn) {
            uploadBtn.classList.add('d-none');
        }
    }

    async uploadFiles() {
        if (this.uploadInProgress || this.files.length === 0) return;

        this.uploadInProgress = true;
        document.getElementById('uploadProgress').classList.remove('d-none');
        document.getElementById('filesContainer').classList.add('d-none');

        const startTime = Date.now();
        let completed = 0;
        const results = [];

        for (let i = 0; i < this.files.length; i++) {
            const file = this.files[i];
            await this.uploadFile(file, i + 1, this.files.length, results);
            completed++;

            // Actualizar progreso
            const progress = (completed / this.files.length) * 100;
            this.updateProgressBar(progress, completed, this.files.length);
        }

        const endTime = Date.now();
        const duration = Math.round((endTime - startTime) / 1000);

        this.showCompletionMessage(completed, duration, results);
        this.uploadInProgress = false;
    }

    async uploadFile(file, current, total, results) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            document.getElementById('currentFile').textContent = `${file.name} (${current}/${total})`;
            this.updateStatus('Iniciando carga...');
            this.setStepActive('ocr');

            const response = await fetch('/api/facturas/procesar', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                const numeroFactura = data.datos_extraidos?.numero_factura || data.numero_factura || 'procesada';
                this.updateStatus(`Procesado: ${numeroFactura}`);
                this.setStepActive('ai');

                results.push({
                    success: true,
                    file: file.name,
                    data: data
                });

                this.setStepActive('save');
            } else {
                // Intentar obtener detalles del error del servidor
                let errorDetail = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorData.message || errorDetail;
                } catch (e) {
                    // Si no se puede parsear JSON, usar status
                }
                throw new Error(errorDetail);
            }
        } catch (error) {
            // Extraer mensaje de error de forma robusta
            let errorMsg = 'Error desconocido';
            
            if (error instanceof Error) {
                errorMsg = error.message || 'Error sin mensaje';
            } else if (typeof error === 'string') {
                errorMsg = error;
            } else if (error && typeof error === 'object') {
                errorMsg = error.message || error.detail || JSON.stringify(error).slice(0, 100) || 'Error desconocido';
            }
            
            console.error(`Error cargando ${file.name}:`, error);
            console.error(`Tipo de error: ${typeof error}`, `Es Error: ${error instanceof Error}`);
            this.addError(`${file.name}: ${errorMsg}`);
            results.push({
                success: false,
                file: file.name,
                error: errorMsg
            });
        }
    }

    updateProgressBar(progress, completed, total) {
        const bar = document.getElementById('progressBar');
        const percent = document.getElementById('progressPercent');

        bar.style.width = progress + '%';
        percent.textContent = Math.round(progress) + '%';
    }

    updateStatus(text) {
        document.getElementById('statusText').textContent = text;
    }

    setStepActive(step) {
        // Actualizar visual de pasos
        const steps = ['ocr', 'ai', 'save'];
        const icons = {
            'ocr': 'bi-arrow-repeat text-primary',
            'ai': 'bi-arrow-repeat text-primary',
            'save': 'bi-arrow-repeat text-primary'
        };

        steps.forEach(s => {
            const elem = document.getElementById(`step-${s}`);
            if (elem) {
                const icon = elem.parentElement.querySelector('i');
                if (s === step) {
                    icon.className = `bi ${icons[s]} me-1`;
                    icon.style.animation = 'spin 0.8s linear infinite';
                } else if (steps.indexOf(s) < steps.indexOf(step)) {
                    icon.className = 'bi bi-check-circle text-success me-1';
                    icon.style.animation = 'none';
                }
            }
        });
    }

    showCompletionMessage(count, duration, results) {
        const progressDiv = document.getElementById('uploadProgress');
        const completeDiv = document.getElementById('uploadComplete');
        const completedCount = document.getElementById('completedCount');
        const completedTime = document.getElementById('completedTime');
        const resultsList = document.getElementById('resultsList');

        progressDiv.classList.add('d-none');
        completeDiv.classList.remove('d-none');

        const successful = results.filter(r => r.success).length;
        completedCount.textContent = `${successful} factura${successful !== 1 ? 's' : ''}`;
        completedTime.textContent = `Tiempo total: ${duration} segundo${duration !== 1 ? 's' : ''}`;

        // Mostrar resultados en tabla
        let tableHTML = `
            <div class="col-12">
                <div class="table-responsive">
                    <table class="table table-hover table-sm mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>No. Factura</th>
                                <th>Proveedor</th>
                                <th>Fecha</th>
                                <th class="text-end">Importe Base</th>
                                <th class="text-end">IVA</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        results.forEach((result, index) => {
            if (result.success) {
                const datos = result.data.datos_extraidos || {};
                const numeroFactura = datos.numero_factura || result.data.numero_factura || 'N/A';
                const fecha = datos.fecha || result.data.fecha || 'N/A';
                const total = datos.total || result.data.total || '0.00';
                const iva = datos.iva || result.data.iva || '0.00';
                const baseImponible = datos.base_imponible || result.data.base_imponible || '0.00';
                const proveedor = datos.proveedor || 'No especificado';
                
                tableHTML += `
                    <tr class="table-success">
                        <td><strong>${numeroFactura}</strong></td>
                        <td>${proveedor}</td>
                        <td>${fecha}</td>
                        <td class="text-end">€${parseFloat(baseImponible).toFixed(2)}</td>
                        <td class="text-end">€${parseFloat(iva).toFixed(2)}</td>
                        <td class="text-end"><strong class="text-success">€${parseFloat(total).toFixed(2)}</strong></td>
                    </tr>
                `;
            } else {
                tableHTML += `
                    <tr class="table-danger">
                        <td colspan="6">
                            <i class="bi bi-exclamation-circle text-danger me-2"></i>
                            ${result.file}: ${result.error}
                        </td>
                    </tr>
                `;
            }
        });

        tableHTML += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        resultsList.innerHTML = tableHTML;

        // Botón para más cargas
        const uploadMoreBtn = document.getElementById('uploadMoreBtn');
        if (uploadMoreBtn) {
            uploadMoreBtn.onclick = () => {
                this.reset();
            };
        }
    }

    addError(message) {
        const errorsList = document.getElementById('errorsList');
        if (errorsList.children.length === 0) {
            errorsList.innerHTML = '';
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        errorsList.appendChild(alertDiv);
    }

    cancelUpload() {
        this.uploadInProgress = false;
        document.getElementById('uploadProgress').classList.add('d-none');
        document.getElementById('filesContainer').classList.remove('d-none');
    }

    reset() {
        this.files = [];
        document.getElementById('uploadProgress').classList.add('d-none');
        document.getElementById('uploadComplete').classList.add('d-none');
        document.getElementById('filesContainer').classList.add('d-none');
        document.getElementById('fileInput').value = '';
        document.getElementById('errorsList').innerHTML = '';
        this.hideUploadButton();
        
        // Resetear pasos visuales
        const steps = ['ocr', 'ai', 'save'];
        steps.forEach(s => {
            const elem = document.getElementById(`step-${s}`);
            if (elem) {
                const icon = elem.parentElement.querySelector('i');
                if (icon) {
                    icon.className = 'bi bi-circle me-1';
                    icon.style.color = '#d1d5db';
                    icon.style.animation = 'none';
                }
            }
        });
    }

    resetUpload() {
        this.reset();
    }
}

// Instanciar el manager globalmente - verificar si DOM ya está listo
if (document.readyState === 'loading') {
    // DOM aún se está cargando, esperar
    document.addEventListener('DOMContentLoaded', () => {
        window.uploadManager = new UploadManager();
    });
} else {
    // DOM ya está listo
    window.uploadManager = new UploadManager();
}
