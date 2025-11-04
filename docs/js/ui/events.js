// ========================================
// EVENT LISTENERS
// ========================================

import { saveSettings } from '../storage.js';
import { validateColorConfiguration, hideValidationWarning } from './validation.js';
import { copyShareURL } from '../urlParams.js';
import { csvInfo } from '../dataLoader.js';
import { DEFAULT_SETTINGS } from '../config.js';
import { updateStatus, sortCommanders } from './display.js';

export function setupEventListeners(handleRandomizeCallback, resetToDefaultSettingsCallback) {
    // Time period change
    document.getElementById('time-period').addEventListener('change', () => {
        updateMaxRankLabel();
        saveSettings();
    });
    
    // Save settings on input changes
    document.getElementById('min-rank').addEventListener('change', saveSettings);
    document.getElementById('max-rank').addEventListener('change', saveSettings);
    document.getElementById('quantity').addEventListener('change', saveSettings);
    document.getElementById('exclude-partners').addEventListener('change', saveSettings);
    document.getElementById('text-output').addEventListener('change', saveSettings);
    
    // Color filter toggle
    document.getElementById('enable-color-filter').addEventListener('change', (e) => {
        const section = document.getElementById('color-filter-section');
        if (e.target.checked) {
            section.classList.remove('hidden');
        } else {
            section.classList.add('hidden');
            hideValidationWarning();
        }
        saveSettings();
    });
    
    // Color checkbox visual feedback
    document.querySelectorAll('.color-input').forEach(input => {
        input.addEventListener('change', (e) => {
            const label = e.target.closest('.color-checkbox');
            if (e.target.checked) {
                label.classList.add('selected');
            } else {
                label.classList.remove('selected');
            }
            validateColorConfiguration();
            saveSettings();
        });
    });
    
    // Validation on mode change
    document.querySelectorAll('input[name="color-mode"]').forEach(input => {
        input.addEventListener('change', () => {
            validateColorConfiguration();
            saveSettings();
        });
    });
    
    // Validation on color count buttons
    document.querySelectorAll('.color-count-input').forEach(input => {
        input.addEventListener('change', (e) => {
            const label = e.target.closest('.color-count-button');
            if (e.target.checked) {
                label.classList.add('selected');
            } else {
                label.classList.remove('selected');
            }
            validateColorConfiguration();
            saveSettings();
        });
    });
    
    // Additional filters toggle
    const additionalFiltersCheckbox = document.getElementById('enable-additional-filters');
    console.log('Additional Filters Checkbox element:', additionalFiltersCheckbox);
    if (additionalFiltersCheckbox) {
        additionalFiltersCheckbox.addEventListener('change', (e) => {
            console.log('Additional filters checkbox changed:', e.target.checked);
            const section = document.getElementById('additional-filters-section');
            console.log('Additional filters section element:', section);
            if (e.target.checked) {
                console.log('Removing hidden class');
                section.classList.remove('hidden');
            } else {
                console.log('Adding hidden class');
                section.classList.add('hidden');
            }
            saveSettings();
        });
    } else {
        console.error('Additional filters checkbox not found!');
    }
    
    // Advanced Randomizer toggle
    const advancedRandomizerCheckbox = document.getElementById('enable-advanced-randomizer');
    if (advancedRandomizerCheckbox) {
        advancedRandomizerCheckbox.addEventListener('change', (e) => {
            const section = document.getElementById('advanced-randomizer-section');
            if (e.target.checked) {
                section.classList.remove('hidden');
            } else {
                section.classList.add('hidden');
            }
            saveSettings();
        });
    }
    
    // Preset buttons - fill in equation when clicked
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const equation = btn.getAttribute('data-equation');
            const { setEquation } = await import('../advancedRandomizer.js');
            setEquation(equation);
            // Auto-resize after setting equation
            autoResizeTextarea(distributionEquationInput);
        });
    });
    
    // Auto-resize function for textarea
    function autoResizeTextarea(textarea) {
        if (!textarea) return;
        // Reset height to auto to get the correct scrollHeight
        textarea.style.height = 'auto';
        // Set height to scrollHeight (content height)
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    // Distribution equation input
    const distributionEquationInput = document.getElementById('distribution-equation');
    if (distributionEquationInput) {
        distributionEquationInput.addEventListener('change', saveSettings);
        distributionEquationInput.addEventListener('blur', saveSettings);
        
        // Auto-resize on input
        distributionEquationInput.addEventListener('input', () => {
            autoResizeTextarea(distributionEquationInput);
        });
        
        // Initial resize on page load
        autoResizeTextarea(distributionEquationInput);
    }
    
    // CMC filter enable toggle
    document.getElementById('enable-cmc-filter').addEventListener('change', saveSettings);
    
    // CMC inputs
    document.getElementById('min-cmc').addEventListener('change', saveSettings);
    document.getElementById('max-cmc').addEventListener('change', saveSettings);
    
    // Salt filter enable toggle
    document.getElementById('enable-salt-filter').addEventListener('change', saveSettings);
    
    // Set filter enable toggle
    document.getElementById('enable-set-filter').addEventListener('change', saveSettings);
    
    // Set filter inputs
    document.getElementById('include-sets').addEventListener('input', saveSettings);
    document.getElementById('exclude-sets').addEventListener('input', saveSettings);
    
    // Salt toggle button
    document.getElementById('salt-toggle').addEventListener('click', () => {
        const btn = document.getElementById('salt-toggle');
        const icon = btn.querySelector('.salt-icon');
        const label = btn.querySelector('.salt-label');
        
        if (btn.classList.contains('salty')) {
            // Switch to chill
            btn.classList.remove('salty');
            btn.classList.add('chill');
            icon.textContent = '❄️';
            label.textContent = 'Chill';
        } else {
            // Switch to salty
            btn.classList.remove('chill');
            btn.classList.add('salty');
            icon.textContent = '🧂';
            label.textContent = 'Salty';
        }
        
        saveSettings();
    });
    
    // Randomize button
    document.getElementById('randomize-btn').addEventListener('click', (e) => {
        e.preventDefault();
        handleRandomizeCallback();
    });
    
    // Reset button
    document.getElementById('reset-btn').addEventListener('click', resetToDefaultSettingsCallback);
    
    // Share Settings button
    document.getElementById('share-btn').addEventListener('click', copyShareURL);
    
    // Share Results button
    const shareResultsBtn = document.getElementById('share-results-btn');
    if (shareResultsBtn) {
        shareResultsBtn.addEventListener('click', async () => {
            const { copyShareResultsURL } = await import('../urlParams.js');
            await copyShareResultsURL();
        });
    }
    
    // Exit Results View button
    const exitResultsBtn = document.getElementById('exit-results-btn');
    if (exitResultsBtn) {
        exitResultsBtn.addEventListener('click', () => {
            import('../storage.js').then(({ exitResultsViewMode }) => {
                exitResultsViewMode();
            });
        });
    }
    
    // Sort buttons
    document.getElementById('sort-rank-btn').addEventListener('click', () => {
        sortCommanders('rank');
    });
    
    document.getElementById('sort-cmc-btn').addEventListener('click', () => {
        sortCommanders('cmc');
    });
}

export function updateMaxRankLabel() {
    const timePeriod = document.getElementById('time-period').value;
    const info = csvInfo[timePeriod];
    
    if (info && info.max_rank) {
        document.getElementById('max-rank-help').textContent = `(Max: ${info.max_rank})`;
        
        // Update max rank if it exceeds the new max
        const maxRankInput = document.getElementById('max-rank');
        const currentMax = parseInt(maxRankInput.value);
        if (currentMax > info.max_rank) {
            maxRankInput.value = info.max_rank;
        }
    }
}

export function getColorFilterSettings() {
    const enabled = document.getElementById('enable-color-filter').checked;
    
    if (!enabled) {
        return { colors: null, color_mode: 'exactly', num_colors: null, selected_color_counts: [] };
    }
    
    // Get selected colors
    const colorInputs = document.querySelectorAll('.color-input:checked');
    const selectedColors = Array.from(colorInputs).map(input => input.value);
    
    // Get color mode
    const colorMode = document.querySelector('input[name="color-mode"]:checked').value;
    
    // Get selected color counts as array (always use checkbox mode now)
    const colorCountInputs = document.querySelectorAll('.color-count-input:checked');
    const selectedColorCounts = Array.from(colorCountInputs).map(input => parseInt(input.value));
    
    // Build colors string
    let colors = null;
    if (selectedColors.length > 0 || selectedColorCounts.length > 0) {
        colors = selectedColors.join(',');
    }
    
    return { colors, color_mode: colorMode, num_colors: null, selected_color_counts: selectedColorCounts };
}

export function getAdditionalFilterSettings() {
    const enabled = document.getElementById('enable-additional-filters').checked;
    
    if (!enabled) {
        return { 
            enable_cmc: false,
            min_cmc: null, 
            max_cmc: null, 
            enable_salt: false,
            salt_mode: null,
            enable_set: false,
            include_sets: [],
            exclude_sets: []
        };
    }
    
    const enableCmc = document.getElementById('enable-cmc-filter').checked;
    const minCmc = parseInt(document.getElementById('min-cmc').value);
    const maxCmc = parseInt(document.getElementById('max-cmc').value);
    
    const enableSalt = document.getElementById('enable-salt-filter').checked;
    const saltBtn = document.getElementById('salt-toggle');
    const saltMode = saltBtn.classList.contains('salty') ? 'salty' : 'chill';
    
    const enableSet = document.getElementById('enable-set-filter').checked;
    const includeSetInput = document.getElementById('include-sets').value.trim();
    const excludeSetInput = document.getElementById('exclude-sets').value.trim();
    
    // Parse set codes - split by comma, trim, uppercase, remove empties
    const includeSets = includeSetInput
        ? includeSetInput.split(',').map(s => s.trim().toUpperCase()).filter(s => s.length > 0)
        : [];
    const excludeSets = excludeSetInput
        ? excludeSetInput.split(',').map(s => s.trim().toUpperCase()).filter(s => s.length > 0)
        : [];
    
    return { 
        enable_cmc: enableCmc,
        min_cmc: enableCmc ? minCmc : null, 
        max_cmc: enableCmc ? maxCmc : null,
        enable_salt: enableSalt,
        salt_mode: enableSalt ? saltMode : null,
        enable_set: enableSet,
        include_sets: enableSet ? includeSets : [],
        exclude_sets: enableSet ? excludeSets : []
    };
}

export function resetToDefaultSettings() {
    console.log('Resetting to default settings...');
    
    // Clear all localStorage
    localStorage.clear();
    
    // Clear URL parameters (return to normal mode)
    const cleanURL = window.location.origin + window.location.pathname;
    window.history.replaceState({}, document.title, cleanURL);
    
    // Apply default settings using the DEFAULT_SETTINGS object
    document.getElementById('time-period').value = DEFAULT_SETTINGS.timePeriod;
    document.getElementById('min-rank').value = DEFAULT_SETTINGS.minRank;
    document.getElementById('max-rank').value = DEFAULT_SETTINGS.maxRank;
    document.getElementById('quantity').value = DEFAULT_SETTINGS.quantity;
    document.getElementById('enable-color-filter').checked = DEFAULT_SETTINGS.enableColorFilter;
    document.getElementById('exclude-partners').checked = DEFAULT_SETTINGS.excludePartners;
    document.getElementById('text-output').checked = DEFAULT_SETTINGS.textOutput;
    
    // Show/hide color filter section based on defaults
    const colorSection = document.getElementById('color-filter-section');
    if (DEFAULT_SETTINGS.enableColorFilter) {
        colorSection.classList.remove('hidden');
    } else {
        colorSection.classList.add('hidden');
    }
    
    // Apply default color selections
    document.querySelectorAll('.color-input').forEach(input => {
        if (DEFAULT_SETTINGS.selectedColors.includes(input.value)) {
            input.checked = true;
            input.closest('.color-checkbox').classList.add('selected');
        } else {
            input.checked = false;
            input.closest('.color-checkbox').classList.remove('selected');
        }
    });
    
    // Apply default color mode
    document.querySelector(`input[name="color-mode"][value="${DEFAULT_SETTINGS.colorMode}"]`).checked = true;
    
    // Apply default color count buttons
    document.querySelectorAll('.color-count-input').forEach(input => {
        if (DEFAULT_SETTINGS.selectedColorCounts.includes(input.value)) {
            input.checked = true;
            input.closest('.color-count-button').classList.add('selected');
        } else {
            input.checked = false;
            input.closest('.color-count-button').classList.remove('selected');
        }
    });
    
    // Reset additional filters
    document.getElementById('enable-additional-filters').checked = DEFAULT_SETTINGS.enableAdditionalFilters;
    document.getElementById('enable-cmc-filter').checked = DEFAULT_SETTINGS.enableCmcFilter;
    document.getElementById('min-cmc').value = DEFAULT_SETTINGS.minCmc;
    document.getElementById('max-cmc').value = DEFAULT_SETTINGS.maxCmc;
    document.getElementById('enable-salt-filter').checked = DEFAULT_SETTINGS.enableSaltFilter;
    document.getElementById('enable-set-filter').checked = DEFAULT_SETTINGS.enableSetFilter;
    document.getElementById('include-sets').value = DEFAULT_SETTINGS.includeSets;
    document.getElementById('exclude-sets').value = DEFAULT_SETTINGS.excludeSets;
    
    // Reset salt toggle button
    const saltBtn = document.getElementById('salt-toggle');
    const saltIcon = saltBtn.querySelector('.salt-icon');
    const saltLabel = saltBtn.querySelector('.salt-label');
    saltBtn.classList.remove('chill', 'salty');
    saltBtn.classList.add(DEFAULT_SETTINGS.saltMode);
    if (DEFAULT_SETTINGS.saltMode === 'salty') {
        saltIcon.textContent = '🧂';
        saltLabel.textContent = 'Salty';
    } else {
        saltIcon.textContent = '❄️';
        saltLabel.textContent = 'Chill';
    }
    
    // Show/hide additional filters section
    const additionalSection = document.getElementById('additional-filters-section');
    if (DEFAULT_SETTINGS.enableAdditionalFilters) {
        additionalSection.classList.remove('hidden');
    } else {
        additionalSection.classList.add('hidden');
    }
    
    // Reset advanced randomizer settings
    document.getElementById('enable-advanced-randomizer').checked = DEFAULT_SETTINGS.enableAdvancedRandomizer;
    document.getElementById('distribution-equation').value = DEFAULT_SETTINGS.distributionEquation;
    
    // Show/hide advanced randomizer section
    const advancedRandomizerSection = document.getElementById('advanced-randomizer-section');
    if (DEFAULT_SETTINGS.enableAdvancedRandomizer) {
        advancedRandomizerSection.classList.remove('hidden');
    } else {
        advancedRandomizerSection.classList.add('hidden');
    }
    
    // Hide validation warning
    hideValidationWarning();
    
    // Update max rank label
    updateMaxRankLabel();
    
    console.log('Reset complete - returned to normal mode');
    updateStatus('Settings reset to defaults');
}
