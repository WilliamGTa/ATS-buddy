// DOM elements - will be initialized after DOM is ready
let resumeFile, fileUploadLabel, fileInfo, deduplicationStatus, fileError;
let jobDescription, charCount, jobDescError, analyzeBtn, analysisForm;
let generalError, resumePreviewSection, resumePreviewText, previewFileInfo;

function initializeDOMElements() {
    resumeFile = document.getElementById('resumeFile');
    fileUploadLabel = document.querySelector('.file-upload-label');
    fileInfo = document.getElementById('fileInfo');
    deduplicationStatus = document.getElementById('deduplicationStatus');
    fileError = document.getElementById('fileError');
    jobDescription = document.getElementById('jobDescription');
    charCount = document.getElementById('charCount');
    jobDescError = document.getElementById('jobDescError');
    analyzeBtn = document.getElementById('analyzeBtn');
    analysisForm = document.getElementById('analysisForm');
    generalError = document.getElementById('generalError');
    resumePreviewSection = document.getElementById('resumePreviewSection');
    resumePreviewText = document.getElementById('resumePreviewText');
    previewFileInfo = document.getElementById('previewFileInfo');
    
    console.log('DOM elements initialized:');
    console.log('- analysisForm:', analysisForm);
    console.log('- analyzeBtn:', analyzeBtn);
    console.log('- resumeFile:', resumeFile);
    console.log('- jobDescription:', jobDescription);
}

// Constants
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
const MIN_JOB_DESC_LENGTH = 100;

// State
let isFileValid = false;
let isJobDescValid = false;

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded');
    
    // Initialize DOM elements first
    initializeDOMElements();
    
    // Wait a bit for DOM to be fully ready
    setTimeout(() => {
        initializeCoverPage();
        initializeEventListeners();
        updateSubmitButton();
    }, 100);
});

function initializeCoverPage() {
    const startBtn = document.getElementById('startAnalysisBtn');
    const backBtn = document.getElementById('backToCoverBtn');
    const coverPage = document.getElementById('coverPage');
    const mainApp = document.getElementById('mainApp');

    if (startBtn) {
        startBtn.addEventListener('click', function () {
            coverPage.classList.add('hidden');
            mainApp.classList.remove('hidden');
            // Smooth scroll to top of main app
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    if (backBtn) {
        backBtn.addEventListener('click', function () {
            mainApp.classList.add('hidden');
            coverPage.classList.remove('hidden');
            // Reset form when going back
            resetToInitialState();
            // Smooth scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
}

function resetToInitialState() {
    // Remove results section
    removeExistingSections();

    // Reset form state
    resetFormState();

    // Clear form data
    resumeFile.value = '';
    resumeFile.droppedFile = null;
    jobDescription.value = '';

    // Reset validation states
    isFileValid = false;
    isJobDescValid = false;

    // Hide all status elements
    hideInfo(fileInfo);
    hideDeduplicationStatus();
    hideResumePreview();
    hideError(fileError);
    hideError(jobDescError);
    hideError(generalError);

    // Reset character count
    charCount.textContent = '0';
    charCount.parentElement.classList.remove('valid');
    jobDescription.classList.remove('valid', 'invalid');

    // Update submit button
    updateSubmitButton();
}

function initializeEventListeners() {
    console.log('Initializing event listeners...');
    console.log('analysisForm:', analysisForm);
    console.log('analyzeBtn:', analyzeBtn);
    
    // Check if elements exist
    if (!analysisForm) {
        console.error('analysisForm not found!');
        return;
    }
    
    if (!analyzeBtn) {
        console.error('analyzeBtn not found!');
        return;
    }

    // File upload events
    if (resumeFile) {
        resumeFile.addEventListener('change', handleFileSelect);
    }

    // Drag and drop events on label
    if (fileUploadLabel) {
        fileUploadLabel.addEventListener('dragover', handleDragOver);
        fileUploadLabel.addEventListener('dragleave', handleDragLeave);
        fileUploadLabel.addEventListener('drop', handleFileDrop);
    }

    // Also add drag and drop events to the container for better coverage
    const fileUploadContainer = document.querySelector('.file-upload-container');
    if (fileUploadContainer) {
        fileUploadContainer.addEventListener('dragover', handleDragOver);
        fileUploadContainer.addEventListener('dragleave', handleDragLeave);
        fileUploadContainer.addEventListener('drop', handleFileDrop);
    }

    // Job description events
    if (jobDescription) {
        jobDescription.addEventListener('input', handleJobDescriptionInput);
        jobDescription.addEventListener('blur', validateJobDescription);
    }

    // Form submission
    analysisForm.addEventListener('submit', handleFormSubmit);
    console.log('Form submission event listener added');
    
    // Also add direct click handler to button as backup
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function(e) {
            console.log('Analyze button clicked directly');
            if (e.target.type !== 'submit') {
                e.preventDefault();
                handleFormSubmit(e);
            }
        });
        console.log('Direct button click listener added');
    }
}

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    validateAndDisplayFile(file);
}

function handleDragOver(event) {
    event.preventDefault();
    fileUploadLabel.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    fileUploadLabel.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    fileUploadLabel.classList.remove('dragover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];

        // Try to update the input element files property
        try {
            // Method 1: Try DataTransfer (modern browsers)
            if (typeof DataTransfer !== 'undefined') {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                resumeFile.files = dataTransfer.files;
            } else {
                // Method 2: Fallback - we'll store the file separately and handle it in form submission
                resumeFile.droppedFile = file;
            }
        } catch (error) {
            // Method 3: Final fallback - store file separately
            console.log('DataTransfer not supported, using fallback method');
            resumeFile.droppedFile = file;
        }

        validateAndDisplayFile(file);
    }
}

function validateAndDisplayFile(file) {
    hideError(fileError);
    hideInfo(fileInfo);
    hideDeduplicationStatus();
    hideResumePreview();

    if (!file) {
        isFileValid = false;
        updateSubmitButton();
        return;
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
        showError(fileError, 'Please select a PDF file only.');
        isFileValid = false;
        updateSubmitButton();
        return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        showError(fileError, `File size (${sizeMB}MB) exceeds the maximum limit of 10MB.`);
        isFileValid = false;
        updateSubmitButton();
        return;
    }

    // File is valid
    isFileValid = true;
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    showInfo(fileInfo, `✓ ${file.name} (${sizeMB}MB) - Ready for analysis`);

    // Show resume preview with file info
    showResumePreview(file);

    updateSubmitButton();
}

// Job description handling functions
function handleJobDescriptionInput(event) {
    const text = event.target.value;
    const length = text.length;

    // Update character count
    charCount.textContent = length;
    const charCountElement = charCount.parentElement;

    if (length >= MIN_JOB_DESC_LENGTH) {
        charCountElement.classList.add('valid');
        jobDescription.classList.remove('invalid');
        jobDescription.classList.add('valid');
    } else {
        charCountElement.classList.remove('valid');
        jobDescription.classList.remove('valid');
        if (length > 0) {
            jobDescription.classList.add('invalid');
        }
    }

    // Validate in real-time but don't show error until blur
    isJobDescValid = length >= MIN_JOB_DESC_LENGTH;
    updateSubmitButton();
}

function validateJobDescription() {
    const text = jobDescription.value.trim();
    const length = text.length;

    hideError(jobDescError);

    if (length === 0) {
        showError(jobDescError, 'Job description is required.');
        isJobDescValid = false;
    } else if (length < MIN_JOB_DESC_LENGTH) {
        const remaining = MIN_JOB_DESC_LENGTH - length;
        showError(jobDescError, `Job description is too short. Please add ${remaining} more characters.`);
        isJobDescValid = false;
    } else {
        isJobDescValid = true;
    }

    updateSubmitButton();
}

// Form submission
function handleFormSubmit(event) {
    console.log('Form submit handler called!');
    event.preventDefault();

    console.log('File valid:', isFileValid);
    console.log('Job desc valid:', isJobDescValid);

    // Final validation
    validateJobDescription();

    if (!isFileValid) {
        console.log('File validation failed');
        showError(generalError, 'Please upload a valid PDF file.');
        return;
    }

    if (!isJobDescValid) {
        console.log('Job description validation failed');
        showError(generalError, 'Please enter a valid job description.');
        return;
    }

    hideError(generalError);

    console.log('Starting analysis...');
    // Start analysis
    startAnalysis();
}

async function startAnalysis() {
    // Get file from input or from dropped file fallback
    const file = resumeFile.files[0] || resumeFile.droppedFile;
    const jobDesc = jobDescription.value.trim();

    // Show loading state
    showLoadingState();

    try {
        // Create form data for API request
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('jobDescription', jobDesc);

        // Make API request
        const response = await fetch(getApiUrl(), {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Check for deduplication status and show if applicable
        if (data.deduplicationStatus) {
            showDeduplicationStatus(data.deduplicationStatus);
        }

        // Show results
        showAnalysisResults(data);

    } catch (error) {
        console.error('Analysis failed:', error);
        showAnalysisError(error.message);
    }
}

function getApiUrl() {
    // Use configured API URL if available
    if (window.ATS_BUDDY_CONFIG && window.ATS_BUDDY_CONFIG.apiUrl) {
        return window.ATS_BUDDY_CONFIG.apiUrl;
    }

    // Fallback for development and production
    const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:3000/dev/analyze'  // Local SAM development
        : 'https://4rvo13bwv1.execute-api.ap-southeast-1.amazonaws.com/dev/analyze';  // Production API Gateway

    return apiUrl;
}

// Loading and results functions
function showLoadingState() {
    // Disable form inputs
    resumeFile.disabled = true;
    jobDescription.disabled = true;
    analyzeBtn.disabled = true;

    // Update button text and show loading
    analyzeBtn.innerHTML = `
        <span class="loading-spinner"></span>
        Analyzing Resume...
    `;
    analyzeBtn.classList.add('loading');

    // Hide any existing errors
    hideError(generalError);

    // Create and show loading section
    createLoadingSection();
}

function createLoadingSection() {
    // Remove existing loading or results sections
    removeExistingSections();

    const loadingSection = document.createElement('section');
    loadingSection.className = 'form-section loading-section';
    loadingSection.id = 'loadingSection';

    loadingSection.innerHTML = `
        <h2>Analyzing Your Resume</h2>
        <div class="loading-container">
            <div class="loading-steps">
                <div class="loading-step active" id="step1">
                    <div class="step-icon">📄</div>
                    <div class="step-text">Extracting text from PDF...</div>
                </div>
                <div class="loading-step" id="step2">
                    <div class="step-icon">🤖</div>
                    <div class="step-text">Analyzing against job requirements...</div>
                </div>
                <div class="loading-step" id="step3">
                    <div class="step-icon">📊</div>
                    <div class="step-text">Generating compatibility report...</div>
                </div>
            </div>
            <div class="loading-progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text">Processing... This may take up to 30 seconds</div>
            </div>
        </div>
    `;

    // Insert after the form
    analysisForm.parentNode.insertBefore(loadingSection, analysisForm.nextSibling);

    // Start progress animation
    animateProgress();
}

function animateProgress() {
    const progressFill = document.getElementById('progressFill');
    const steps = document.querySelectorAll('.loading-step');
    let currentStep = 0;
    let progress = 0;

    const interval = setInterval(() => {
        progress += 2;
        progressFill.style.width = `${Math.min(progress, 90)}%`;

        // Update active step
        if (progress > 30 && currentStep === 0) {
            steps[0].classList.remove('active');
            steps[0].classList.add('completed');
            steps[1].classList.add('active');
            currentStep = 1;
        } else if (progress > 60 && currentStep === 1) {
            steps[1].classList.remove('active');
            steps[1].classList.add('completed');
            steps[2].classList.add('active');
            currentStep = 2;
        }

        // Stop at 90% and wait for actual completion
        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 200);

    // Store interval ID for cleanup
    window.loadingInterval = interval;
}

function showAnalysisResults(data) {
    // Complete the loading animation
    completeLoading();

    // Update resume preview with extracted text if available
    if (data.originalResumeText) {
        updateResumePreview(data.originalResumeText);
    }

    // Reset form state to remove spinner and re-enable form
    resetFormState();

    // Remove loading section after a brief delay
    setTimeout(() => {
        removeExistingSections();
        createResultsSection(data);
    }, 1000);
}

function completeLoading() {
    const progressFill = document.getElementById('progressFill');
    const steps = document.querySelectorAll('.loading-step');

    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }

    // Complete progress bar
    if (progressFill) {
        progressFill.style.width = '100%';
    }

    // Mark all steps as completed
    steps.forEach(step => {
        step.classList.remove('active');
        step.classList.add('completed');
    });
}

function createResultsSection(data) {
    const resultsSection = document.createElement('section');
    resultsSection.className = 'form-section results-section';
    resultsSection.id = 'resultsSection';

    resultsSection.innerHTML = `
        <h2>Analysis Results</h2>
        <div class="results-container">
            ${createCompatibilityScoreHTML(data.compatibilityScore)}
            ${createMissingKeywordsHTML(data.missingKeywords)}
            ${createMissingSkillsHTML(data.missingSkills)}
            ${createSuggestionsHTML(data.suggestions)}
            ${createStrengthsHTML(data.strengths)}
            ${createEnhancementHTML(data)}
            ${createReportsHTML(data.reports)}
            ${createNewAnalysisButtonHTML()}
        </div>
    `;

    // Insert after the form
    analysisForm.parentNode.insertBefore(resultsSection, analysisForm.nextSibling);

    // Add event listener for new analysis button
    document.getElementById('newAnalysisBtn').addEventListener('click', startNewAnalysis);

    // Add event listener for enhancement button if available
    const enhanceBtn = document.getElementById('generateEnhancedBtn');
    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', handleEnhancementRequest);

        // Store analysis data for enhancement
        enhanceBtn.analysisData = {
            originalResumeText: data.originalResumeText,
            jobDescription: jobDescription.value.trim(),
            analysisData: {
                compatibility_score: data.compatibilityScore,
                missing_keywords: data.missingKeywords,
                missing_technical_skills: data.missingSkills.technical,
                missing_soft_skills: data.missingSkills.soft,
                suggestions: data.suggestions,
                strengths: data.strengths
            }
        };
    }
}

function createCompatibilityScoreHTML(score) {
    const scoreClass = score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'fair' : 'poor';

    return `
        <div class="result-item compatibility-score">
            <h3>Compatibility Score</h3>
            <div class="score-container">
                <div class="score-circle ${scoreClass}">
                    <span class="score-number">${score}</span>
                    <span class="score-percent">%</span>
                </div>
                <div class="score-description">
                    ${getScoreDescription(score)}
                </div>
            </div>
        </div>
    `;
}

function createMissingKeywordsHTML(keywords) {
    if (!keywords || keywords.length === 0) {
        return `
            <div class="result-item missing-keywords">
                <h3>Missing Keywords</h3>
                <div class="no-issues">✅ Great! No critical keywords missing.</div>
            </div>
        `;
    }

    return `
        <div class="result-item missing-keywords">
            <h3>Missing Keywords</h3>
            <div class="keywords-list">
                ${keywords.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('')}
            </div>
        </div>
    `;
}

function createMissingSkillsHTML(skills) {
    const hasTechnical = skills.technical && skills.technical.length > 0;
    const hasSoft = skills.soft && skills.soft.length > 0;

    if (!hasTechnical && !hasSoft) {
        return `
            <div class="result-item missing-skills">
                <h3>Missing Skills</h3>
                <div class="no-issues">✅ All key skills are well represented.</div>
            </div>
        `;
    }

    return `
        <div class="result-item missing-skills">
            <h3>Missing Skills</h3>
            ${hasTechnical ? `
                <div class="skills-category">
                    <h4>Technical Skills</h4>
                    <div class="skills-list">
                        ${skills.technical.map(skill => `<span class="skill-tag technical">${skill}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            ${hasSoft ? `
                <div class="skills-category">
                    <h4>Soft Skills</h4>
                    <div class="skills-list">
                        ${skills.soft.map(skill => `<span class="skill-tag soft">${skill}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function createSuggestionsHTML(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        return `
            <div class="result-item suggestions">
                <h3>Suggestions</h3>
                <div class="no-issues">✅ Your resume looks great! No specific suggestions at this time.</div>
            </div>
        `;
    }

    return `
        <div class="result-item suggestions">
            <h3>Suggestions for Improvement</h3>
            <ul class="suggestions-list">
                ${suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
            </ul>
        </div>
    `;
}

function createStrengthsHTML(strengths) {
    if (!strengths || strengths.length === 0) {
        return '';
    }

    return `
        <div class="result-item strengths">
            <h3>Your Strengths</h3>
            <ul class="strengths-list">
                ${strengths.map(strength => `<li>✅ ${strength}</li>`).join('')}
            </ul>
        </div>
    `;
}

function createReportsHTML(reports) {
    if (!reports) {
        return '';
    }

    return `
        <div class="result-item reports">
            <h3>Download Reports</h3>
            <div class="reports-buttons">
                ${reports.html ? `
                    <a href="${reports.html.downloadUrl}" target="_blank" class="report-btn html-report">
                        📄 Download HTML Report
                    </a>
                ` : ''}
                ${reports.markdown ? `
                    <a href="${reports.markdown.downloadUrl}" target="_blank" class="report-btn markdown-report">
                        📝 Download Markdown Report
                    </a>
                ` : ''}
            </div>
        </div>
    `;
}

function createEnhancementHTML(data) {
    // Always show enhancement option for completed analysis
    return `
        <div class="result-item enhancement">
            <h3>Enhanced Resume Generation</h3>
            <div class="enhancement-container">
                <p>Generate an improved version of your resume that incorporates missing keywords and optimization suggestions.</p>
                <button id="generateEnhancedBtn" class="enhance-btn">
                    ✨ Generate Enhanced Resume
                </button>
                <div id="enhancedResumeResult" class="enhanced-result hidden"></div>
            </div>
        </div>
    `;
}

function createNewAnalysisButtonHTML() {
    return `
        <div class="result-item new-analysis">
            <button id="newAnalysisBtn" class="new-analysis-btn">
                🔄 Analyze Another Resume
            </button>
        </div>
    `;
}

function showAnalysisError(errorMessage) {
    // Complete loading animation
    completeLoading();

    // Remove loading section
    setTimeout(() => {
        removeExistingSections();

        // Reset form state
        resetFormState();

        // Show error message
        showError(generalError, `Analysis failed: ${errorMessage}`);
    }, 1000);
}

function startNewAnalysis() {
    // Remove results section
    removeExistingSections();

    // Reset form state
    resetFormState();

    // Clear form data
    resumeFile.value = '';
    resumeFile.droppedFile = null; // Clear dropped file fallback
    jobDescription.value = '';

    // Reset validation states
    isFileValid = false;
    isJobDescValid = false;

    // Hide file info and reset UI
    hideInfo(fileInfo);
    hideDeduplicationStatus();
    hideResumePreview();
    hideError(fileError);
    hideError(jobDescError);
    hideError(generalError);

    // Reset character count
    charCount.textContent = '0';
    charCount.parentElement.classList.remove('valid');
    jobDescription.classList.remove('valid', 'invalid');

    // Update submit button
    updateSubmitButton();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetFormState() {
    // Re-enable form inputs
    resumeFile.disabled = false;
    jobDescription.disabled = false;
    analyzeBtn.disabled = !(isFileValid && isJobDescValid);

    // Reset button text and state
    analyzeBtn.innerHTML = 'Analyze Resume';
    analyzeBtn.classList.remove('loading');
}

function removeExistingSections() {
    const existingLoading = document.getElementById('loadingSection');
    const existingResults = document.getElementById('resultsSection');

    if (existingLoading) {
        existingLoading.remove();
    }

    if (existingResults) {
        existingResults.remove();
    }

    // Clear any running intervals
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
    }
}

function getScoreDescription(score) {
    if (score >= 80) return 'Excellent match! Your resume aligns very well with the job requirements.';
    if (score >= 60) return 'Good match! Your resume meets most of the job requirements.';
    if (score >= 40) return 'Fair match. Consider addressing the missing keywords and skills.';
    return 'Needs improvement. Focus on adding the missing keywords and skills highlighted below.';
}

// Utility functions
function updateSubmitButton() {
    analyzeBtn.disabled = !(isFileValid && isJobDescValid);
}

function showError(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
}

function hideError(element) {
    element.classList.add('hidden');
}

function showInfo(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
}

function hideInfo(element) {
    element.classList.add('hidden');
}

// Deduplication status functions
function showDeduplicationStatus(status) {
    let message = '';
    let icon = '';

    if (status === 'deduplicated') {
        message = '⚡ Resume already processed - using cached data (faster processing)';
        icon = '🔄';
    } else if (status === 'cached') {
        message = '💾 Using cached resume data - processing optimized';
        icon = '⚡';
    }

    if (message) {
        deduplicationStatus.innerHTML = `${icon} ${message}`;
        deduplicationStatus.classList.remove('hidden');
        deduplicationStatus.classList.add('deduplication-active');
    }
}

function hideDeduplicationStatus() {
    deduplicationStatus.classList.add('hidden');
}

// Resume preview functions
function showResumePreview(file) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    const uploadDate = new Date().toLocaleDateString();

    // Update file info in preview header
    previewFileInfo.innerHTML = `
        <span><strong>Filename:</strong> ${file.name}</span>
        <span><strong>Size:</strong> ${sizeMB} MB</span>
        <span><strong>Upload Date:</strong> ${uploadDate}</span>
    `;

    // Show preview section
    resumePreviewSection.style.display = 'block';

    // Extract text from PDF for preview (simplified - in real implementation this would be done server-side)
    resumePreviewText.value = 'PDF text extraction will be performed during analysis. Preview will be available after processing.';
}

function hideResumePreview() {
    resumePreviewSection.style.display = 'none';
    resumePreviewText.value = '';
    previewFileInfo.innerHTML = '';
}

function updateResumePreview(extractedText) {
    if (extractedText && resumePreviewSection.style.display === 'block') {
        resumePreviewText.value = extractedText;
    }
}

// Additional validation helpers
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function handleEnhancementRequest(event) {
    const button = event.target;
    const analysisData = button.analysisData;

    if (!analysisData) {
        showError(generalError, 'Enhancement data not available. Please run analysis again.');
        return;
    }

    // Show loading state
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner"></span> Generating Enhanced Resume...';

    try {
        // Make enhancement request
        const response = await fetch(getEnhanceApiUrl(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(analysisData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Show enhanced resume in modal
        showEnhancedResume(data);
        
        // Also show enhanced resume in main results area (persistent)
        showEnhancedResumeInResults(data);

    } catch (error) {
        console.error('Enhancement failed:', error);
        showError(generalError, `Enhancement failed: ${error.message}`);
    } finally {
        // Update button to show it's available and change its behavior
        button.disabled = false;
        button.innerHTML = '👁️ View Enhanced Resume';
        button.classList.add('enhanced-available');
        
        // Remove the old event listener and add new one for viewing
        button.removeEventListener('click', handleEnhancementRequest);
        button.addEventListener('click', function() {
            if (window.currentEnhancedResumeData) {
                showEnhancedResume(window.currentEnhancedResumeData);
            }
        });
    }
}

function getEnhanceApiUrl() {
    // Use configured API URL if available
    if (window.ATS_BUDDY_CONFIG && window.ATS_BUDDY_CONFIG.apiUrl) {
        return window.ATS_BUDDY_CONFIG.apiUrl.replace('/analyze', '/enhance');
    }

    // Fallback for development and production
    const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:3000/dev/enhance'  // Local SAM development
        : 'https://4rvo13bwv1.execute-api.ap-southeast-1.amazonaws.com/dev/enhance';  // Production API Gateway

    return apiUrl;
}

// Enhanced Resume Modal Functions - REDESIGNED FOR BETTER VISIBILITY
function showEnhancedResume(data) {
    // Create full-page modal for enhanced resume
    const modal = document.createElement('div');
    modal.className = 'enhanced-resume-modal';
    modal.id = 'enhancedResumeModal';

    // Check for token cutoff warning
    const tokenWarning = data.tokenCutoffDetected ? `
        <div class="token-warning">
            ⚠️ <strong>Token Limit Warning:</strong> The enhanced resume may have been truncated due to length limits. 
            Consider breaking your resume into smaller sections for better results.
            <br><small>Token limit: ${data.tokenLimitUsed || 8000} | Response length: ${data.responseLength || data.enhancedLength} characters</small>
        </div>
    ` : '';

    modal.innerHTML = `
        <div class="enhanced-resume-modal-content">
            <!-- Header -->
            <div class="enhanced-resume-header">
                <h2>✨ Enhanced Resume</h2>
                <button class="close-modal-btn" onclick="closeEnhancedResumeModal()">✕</button>
            </div>
            
            ${tokenWarning}
            
            <!-- Main Content Area - Resume Display -->
            <div class="resume-main-content">
                <div class="resume-display-container">
                    <div class="resume-preview" id="resumePreview">
                        <pre class="resume-text" id="resumeText">${data.enhancedResume || 'Enhanced resume content not available'}</pre>
                    </div>
                    <textarea class="resume-editor hidden" id="resumeEditor">${data.enhancedResume || ''}</textarea>
                </div>
            </div>
            
            <!-- Sidebar with Stats and Details -->
            <div class="resume-sidebar">
                <!-- Quick Stats -->
                <div class="stats-section">
                    <h3>📊 Enhancement Stats</h3>
                    <div class="stat-grid">
                        <div class="stat-item">
                            <span class="stat-number">${data.originalLength || 0}</span>
                            <span class="stat-label">Original Chars</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.enhancedLength || 0}</span>
                            <span class="stat-label">Enhanced Chars</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.keywordsAdded ? data.keywordsAdded.length : 0}</span>
                            <span class="stat-label">Keywords Added</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.improvementsMade ? data.improvementsMade.length : 0}</span>
                            <span class="stat-label">Improvements</span>
                        </div>
                    </div>
                </div>
                
                <!-- Collapsible Keywords Section -->
                <div class="accordion-section">
                    <button class="accordion-header" onclick="toggleAccordion('keywords')">
                        <span>🔑 Keywords Added (${data.keywordsAdded ? data.keywordsAdded.length : 0})</span>
                        <span class="accordion-icon">▼</span>
                    </button>
                    <div class="accordion-content" id="keywords-content">
                        <div class="keywords-tags">
                            ${data.keywordsAdded && data.keywordsAdded.length > 0 ?
            data.keywordsAdded.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('') :
            '<span class="no-keywords">No additional keywords needed</span>'
        }
                        </div>
                    </div>
                </div>
                
                <!-- Collapsible Improvements Section -->
                <div class="accordion-section">
                    <button class="accordion-header" onclick="toggleAccordion('improvements')">
                        <span>🔧 Improvements Made (${data.improvementsMade ? data.improvementsMade.length : 0})</span>
                        <span class="accordion-icon">▼</span>
                    </button>
                    <div class="accordion-content" id="improvements-content">
                        <ul class="improvements-list">
                            ${data.improvementsMade && data.improvementsMade.length > 0 ?
            data.improvementsMade.map(improvement => `<li>${improvement}</li>`).join('') :
            '<li>General content enhancement and optimization</li>'
        }
                        </ul>
                    </div>
                </div>
                
                <!-- Footer Actions -->
                <div class="sidebar-footer">
                    <div class="sidebar-actions">
                        <button class="action-btn copy-btn full-width" onclick="copyEnhancedResume()">
                            📋 Copy Resume
                        </button>
                        <button class="action-btn download-btn full-width" onclick="downloadEnhancedResume()">
                            💾 Download Resume
                        </button>
                        <button class="action-btn edit-btn full-width" onclick="toggleEditMode()">
                            ✏️ Edit Resume
                        </button>
                    </div>
                    <button class="action-btn secondary-btn full-width" onclick="closeEnhancedResumeModal()">
                        Close Modal
                    </button>
                </div>
            </div>
        </div>
    `;

    // Append modal to body
    document.body.appendChild(modal);

    // Show modal with animation
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);

    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';

    // Add click outside to close
    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeEnhancedResumeModal();
        }
    });

    // Add escape key to close
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && document.getElementById('enhancedResumeModal')) {
            closeEnhancedResumeModal();
        }
    });
}

function closeEnhancedResumeModal() {
    const modal = document.getElementById('enhancedResumeModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function copyEnhancedResume() {
    const resumeText = document.getElementById('resumeText').textContent;
    const copyBtn = document.querySelector('.copy-btn');

    navigator.clipboard.writeText(resumeText).then(() => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        copyBtn.classList.add('copied');

        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = resumeText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);

        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    });
}

function downloadEnhancedResume() {
    const resumeText = document.getElementById('resumeText').textContent;
    const blob = new Blob([resumeText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `enhanced-resume-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function toggleEditMode() {
    const preview = document.getElementById('resumePreview');
    const editor = document.getElementById('resumeEditor');
    const editBtn = document.querySelector('.edit-btn');

    if (preview.classList.contains('hidden')) {
        // Switch to preview mode
        const editedText = editor.value;
        document.getElementById('resumeText').textContent = editedText;
        preview.classList.remove('hidden');
        editor.classList.add('hidden');
        editBtn.innerHTML = '✏️ Edit';
    } else {
        // Switch to edit mode
        const currentText = document.getElementById('resumeText').textContent;
        editor.value = currentText;
        preview.classList.add('hidden');
        editor.classList.remove('hidden');
        editBtn.innerHTML = '👁️ Preview';
        editor.focus();
    }
}

function toggleAccordion(section) {
    const content = document.getElementById(`${section}-content`);
    const icon = document.querySelector(`[onclick="toggleAccordion('${section}')"] .accordion-icon`);

    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        icon.textContent = '▼';
    } else {
        content.classList.add('expanded');
        icon.textContent = '▲';
    }
}

// Show Enhanced Resume in Main Results Area (Persistent)
function showEnhancedResumeInResults(data) {
    const enhancedResumeResult = document.getElementById('enhancedResumeResult');
    
    if (!enhancedResumeResult) {
        console.error('Enhanced resume result container not found');
        return;
    }
    
    // Show the enhanced result container
    enhancedResumeResult.classList.remove('hidden');
    
    // Store the enhanced resume data globally for reuse
    window.currentEnhancedResumeData = data;
    
    // Scroll to the enhanced resume section
    enhancedResumeResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Functions for inline enhanced resume actions
function copyEnhancedResumeInline() {
    const textarea = document.getElementById('enhancedResumeTextInline');
    const copyBtn = document.querySelector('.copy-btn-inline');
    
    if (!textarea || !copyBtn) return;
    
    navigator.clipboard.writeText(textarea.value).then(() => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        copyBtn.classList.add('copied');
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        // Fallback for older browsers
        textarea.select();
        document.execCommand('copy');
        
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    });
}

function downloadEnhancedResumeInline() {
    const textarea = document.getElementById('enhancedResumeTextInline');
    if (!textarea) return;
    
    const resumeText = textarea.value;
    const blob = new Blob([resumeText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `enhanced-resume-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function reopenEnhancedResumeModal() {
    if (window.currentEnhancedResumeData) {
        showEnhancedResume(window.currentEnhancedResumeData);
    }
}