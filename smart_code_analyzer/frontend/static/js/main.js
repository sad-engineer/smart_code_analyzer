let selectedFiles = [];
const allowedExts = ['.py'];

function addFiles(files) {
    files.forEach(file => {
        console.log('Добавляется файл:', file.name, file.webkitRelativePath, file);
        // Если есть относительный путь — сравниваем только по нему
        if (file.webkitRelativePath) {
            if (!selectedFiles.some(f => f.webkitRelativePath === file.webkitRelativePath)) {
                selectedFiles.push(file);
            }
        } else {
            // Если относительного пути нет — сравниваем по имени
            if (!selectedFiles.some(f => !f.webkitRelativePath && f.name === file.name)) {
                selectedFiles.push(file);
            }
        }
    });
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    if (selectedFiles.length === 0) return;
    // Создаём раскрывающийся блок
    const details = document.createElement('details');
    details.className = 'mb-2 bg-white rounded-lg shadow';
    // Заголовок
    const summary = document.createElement('summary');
    summary.className = 'flex items-center justify-between px-4 py-3 cursor-pointer select-none rounded-t-lg bg-gray-100 hover:bg-gray-200';
    summary.innerHTML = `<span class="font-semibold text-gray-800">Выбранные файлы (${selectedFiles.length})</span>`;
    details.appendChild(summary);
    // Список файлов
    const filesDiv = document.createElement('div');
    filesDiv.className = 'p-2 border-t border-gray-200';
    selectedFiles.forEach((file, idx) => {
        const displayPath = (file.webkitRelativePath || file.fullPath || file.name).replace(/^\/+/,'');
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between bg-gray-50 p-2 rounded mb-1';
        div.innerHTML = `
            <span class="text-gray-700">${displayPath}</span>
            <button type="button" data-idx="${idx}" class="text-red-500 hover:text-red-700">✕</button>
        `;
        filesDiv.appendChild(div);
    });
    details.appendChild(filesDiv);
    fileList.appendChild(details);
    fileList.querySelectorAll('button[data-idx]').forEach(btn => {
        btn.onclick = function() {
            const idx = parseInt(this.getAttribute('data-idx'));
            selectedFiles.splice(idx, 1);
            updateFileList();
        };
    });
}

function handleInputChange(input) {
    const files = Array.from(input.files).filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        return allowedExts.includes('.' + ext);
    });
    addFiles(files);
    updateFileList();
}

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
        alert('Пожалуйста, выберите файл или папку');
        return;
    }
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    try {
        const response = await fetch('/analyzer/analyze', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        document.getElementById('results').classList.remove('hidden');
        const resultsDiv = document.getElementById('analysisResults');
        resultsDiv.innerHTML = '';
        
        for (const [filename, result] of Object.entries(data)) {
            // Создаём раскрывающийся блок
            const details = document.createElement('details');
            details.className = 'mb-4 bg-white rounded-lg shadow';

            // Заголовок-строка
            const summary = document.createElement('summary');
            summary.className = 'flex items-center justify-between px-4 py-3 cursor-pointer select-none rounded-t-lg bg-gray-100 hover:bg-gray-200';
            summary.innerHTML = `
                <span class="text-lg font-semibold text-gray-800">${filename === 'summary' ? 'Общая сводка' : filename}</span>
                <span class="px-2 py-1 text-sm rounded ${result.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                    ${result.status}
                </span>
            `;
            details.appendChild(summary);

            // Контент анализа
            if (result.html) {
                const analysisContent = document.createElement('div');
                analysisContent.className = 'p-4 border-t border-gray-200';
                analysisContent.innerHTML = result.html;
                details.appendChild(analysisContent);
            }

            // summary — в начало, остальные — в конец
            if (filename === 'summary') {
                resultsDiv.insertBefore(details, resultsDiv.firstChild);
                details.setAttribute('open', '');
            } else {
                resultsDiv.appendChild(details);
            }
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при анализе файлов');
    }
});

// Drag and drop для одной зоны
const dropZone = document.querySelector('.border-dashed');
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => highlight(dropZone), false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => unhighlight(dropZone), false);
});
dropZone.addEventListener('drop', async (e) => handleDrop(e), false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}
function highlight(element) {
    element.classList.add('border-blue-500');
}
function unhighlight(element) {
    element.classList.remove('border-blue-500');
}
async function handleDrop(e) {
    const dt = e.dataTransfer;
    const items = dt.items;
    if (items && items.length > 0 && items[0].webkitGetAsEntry) {
        const entries = [];
        for (let i = 0; i < items.length; i++) {
            const entry = items[i].webkitGetAsEntry();
            if (entry) entries.push(entry);
        }
        const files = await getFilesFromEntries(entries);
        addFiles(files);
        updateFileList();
    } else {
        const files = Array.from(dt.files).filter(file => {
            const ext = file.name.split('.').pop().toLowerCase();
            return allowedExts.includes('.' + ext);
        });
        addFiles(files);
        updateFileList();
    }
}

async function getFilesFromEntries(entries) {
    let files = [];
    for (const entry of entries) {
        if (entry.isFile) {
            files.push(await getFileFromEntry(entry));
        } else if (entry.isDirectory) {
            files = files.concat(await readAllFilesFromDirectory(entry));
        }
    }
    return files.filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        return allowedExts.includes('.' + ext);
    });
}

function getFileFromEntry(entry) {
    return new Promise(resolve => {
        entry.file(file => {
            file.webkitRelativePath = entry.fullPath;
            resolve(file);
        });
    });
}

function readAllFilesFromDirectory(directoryEntry) {
    return new Promise(resolve => {
        const dirReader = directoryEntry.createReader();
        let entries = [];
        function readEntries() {
            dirReader.readEntries(async results => {
                if (!results.length) {
                    const files = await getFilesFromEntries(entries);
                    resolve(files);
                } else {
                    entries = entries.concat(Array.from(results));
                    readEntries();
                }
            });
        }
        readEntries();
    });
} 