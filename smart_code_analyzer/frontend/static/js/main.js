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
        
        const fileCount = Object.keys(data).filter(key => key !== 'summary').length;

        for (const [filename, result] of Object.entries(data)) {
            // Если один файл — пропускаем summary
            if (fileCount === 1 && filename === 'summary') continue;
            // Если несколько файлов — пропускаем одиночный файл на этом этапе (он будет ниже)
            if (fileCount > 1 && filename === 'summary') {
                // Создаём summary-блок и раскрываем его
                const details = document.createElement('details');
                details.className = 'mb-4 bg-white rounded-lg shadow';
                details.setAttribute('open', '');
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
                let analysisContent = null;
                if (result.html) {
                    analysisContent = document.createElement('div');
                    analysisContent.className = 'p-4 border-t border-gray-200';
                    analysisContent.innerHTML = result.html;
                    details.appendChild(analysisContent);
                }

                // Кнопка ИИ-анализа (широкая)
                const aiBtn = document.createElement('button');
                aiBtn.textContent = 'ИИ-анализ структуры';
                aiBtn.className = 'mt-3 px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition block w-full font-semibold';
                aiBtn.onclick = async () => {
                    aiBtn.disabled = true;
                    aiBtn.innerHTML = 'Анализ... <span class="spinner"></span>';

                    // Собираем все файлы для анализа пакета
                    // selectedFiles — это массив File, нужно получить их содержимое
                    const filesForPackage = await getFilesWithContent(selectedFiles);

                    try {
                        const resp = await fetch('/analyzer/ai-analyze-package', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ files: filesForPackage })
                        });
                        const aiData = await resp.json();
                        let aiDiv = details.querySelector('.ai-analysis');
                        if (!aiDiv) {
                            aiDiv = document.createElement('div');
                            aiDiv.className = 'ai-analysis mt-3 p-3 bg-violet-50 rounded text-sm';
                            details.appendChild(aiDiv);
                        }
                        aiDiv.innerHTML = `
                            <div class="font-bold text-violet-700 mb-2 text-lg">ИИ-анализ структуры пакета</div>
                            <div class="mb-2"><b>Архитектура:</b> <div>${aiData.architecture || '-'}</div></div>
                            <div class="mb-2"><b>Связи между модулями:</b> <div>${aiData.module_relations || '-'}</div></div>
                            <div class="mb-2"><b>Сильные стороны:</b> <div>${aiData.strong_points || '-'}</div></div>
                            <div class="mb-2"><b>Слабые стороны:</b> <div>${aiData.weak_points || '-'}</div></div>
                            <div class="mb-2"><b>Рекомендации:</b> <div>${aiData.recommendations || '-'}</div></div>
                            ${aiData.error ? `<div class="text-red-600">Ошибка: ${aiData.error}</div>` : ''}
                        `;
                    } catch (e) {
                        alert('Ошибка ИИ-анализа структуры пакета');
                    }
                    aiBtn.disabled = false;
                    aiBtn.textContent = 'ИИ-анализ структуры';
                };

                // Добавляем кнопку после анализа
                details.appendChild(aiBtn);

                resultsDiv.insertBefore(details, resultsDiv.firstChild);
                continue;
            }

            // Для одиночного файла или для каждого файла при мультизагрузке
            const details = document.createElement('details');
            details.className = 'mb-4 bg-white rounded-lg shadow';
            if (fileCount === 1) details.setAttribute('open', ''); // раскрываем если один файл

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
            let analysisContent = null;
            if (result.html) {
                analysisContent = document.createElement('div');
                analysisContent.className = 'p-4 border-t border-gray-200';
                analysisContent.innerHTML = result.html;
                details.appendChild(analysisContent);
            }

            // Кнопка ИИ-анализа (широкая)
            const aiBtn = document.createElement('button');
            aiBtn.textContent = 'ИИ-анализ';
            aiBtn.className = 'mt-3 px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition block w-full font-semibold';
            aiBtn.onclick = async () => {
                aiBtn.disabled = true;
                aiBtn.innerHTML = 'Анализ... <span class="spinner"></span>';
                const file = selectedFiles.find(f => f.name === filename || f.webkitRelativePath === filename);
                if (!file) {
                    alert('Файл не найден для ИИ-анализа');
                    aiBtn.disabled = false;
                    aiBtn.textContent = 'ИИ-анализ';
                    return;
                }
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const resp = await fetch('/analyzer/ai-analyze', {
                        method: 'POST',
                        body: formData
                    });
                    const aiData = await resp.json();
                    let aiDiv = details.querySelector('.ai-analysis');
                    if (!aiDiv) {
                        aiDiv = document.createElement('div');
                        aiDiv.className = 'ai-analysis mt-3 p-3 bg-violet-50 rounded text-sm';
                        details.appendChild(aiDiv);
                    }
                    aiDiv.innerHTML = `
                        <div class="font-bold text-violet-700 mb-2 text-lg">ИИ-анализ</div>
                        <div class="mb-2">
                            <span class="font-semibold text-gray-700">Стиль кода:</span>
                            <ul class="list-disc pl-6 text-gray-800">
                                <li><b>Форматирование:</b> ${aiData.code_style.formatting}</li>
                                <li><b>Именование:</b> ${aiData.code_style.naming}</li>
                                <li><b>Документация:</b> ${aiData.code_style.documentation}</li>
                                <li><b>Структура:</b> ${aiData.code_style.structure}</li>
                            </ul>
                        </div>
                        <div class="mb-2">
                            <span class="font-semibold text-gray-700">SOLID:</span>
                            <ul class="list-disc pl-6 text-gray-800">
                                <li><b>SRP:</b> ${aiData.solid_principles.SRP}</li>
                                <li><b>OCP:</b> ${aiData.solid_principles.OCP}</li>
                                <li><b>LSP:</b> ${aiData.solid_principles.LSP}</li>
                                <li><b>ISP:</b> ${aiData.solid_principles.ISP}</li>
                                <li><b>DIP:</b> ${aiData.solid_principles.DIP}</li>
                            </ul>
                        </div>
                        <div class="mb-2">
                            <span class="font-semibold text-gray-700">Потенциальные проблемы:</span>
                            <ul class="list-disc pl-6 text-gray-800">
                                ${aiData.potential_issues && aiData.potential_issues.length > 0
                                    ? aiData.potential_issues.map(issue => `
                                        <li>
                                            <b>${issue.type}:</b> ${issue.description}
                                            <div class="text-gray-600 text-sm ml-2"><b>Рекомендация:</b> ${issue.recommendation}</div>
                                        </li>
                                    `).join('')
                                    : '<li>Не обнаружено</li>'
                                }
                            </ul>
                        </div>
                        <div class="mb-2">
                            <span class="font-semibold text-gray-700">Рекомендации по улучшению:</span>
                            <ul class="list-disc pl-6 text-gray-800">
                                ${aiData.recommendations && aiData.recommendations.length > 0
                                    ? aiData.recommendations.map(rec => `<li>${rec}</li>`).join('')
                                    : '<li>Нет рекомендаций</li>'
                                }
                            </ul>
                        </div>
                        <div class="mt-2 font-bold text-right">
                            <span class="text-gray-700">Общая оценка:</span>
                            <span class="inline-block px-3 py-1 rounded bg-violet-200 text-violet-900 ml-2">${(aiData.overall_score * 100).toFixed(0)} / 100</span>
                        </div>
                    `;
                } catch (e) {
                    alert('Ошибка ИИ-анализа');
                }
                aiBtn.disabled = false;
                aiBtn.textContent = 'ИИ-анализ';
            };

            // Добавляем кнопку после анализа
            details.appendChild(aiBtn);

                resultsDiv.appendChild(details);
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

async function getFilesWithContent(files) {
    const readFile = file =>
        new Promise(resolve => {
            const reader = new FileReader();
            reader.onload = e => resolve({
                filename: file.name,
                content: e.target.result,
                relative_path: file.webkitRelativePath || file.name
            });
            reader.readAsText(file);
        });
    return Promise.all(files.map(readFile));
} 