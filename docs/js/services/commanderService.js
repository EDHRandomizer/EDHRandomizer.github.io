// ========================================
// COMMANDER SERVICE
// ========================================

import { CSV_FILES } from '../config.js';
import { loadCSV } from '../dataLoader.js';
import { selectRandomCommanders, selectRandomCommandersWeighted } from '../commanderFilters.js';
import { commanderNameToUrl } from '../api/edhrec.js';
import { getCardImageUrl } from '../api/scryfall.js';
import { displayTextResults, displayCardImagesProgressive, clearResults, updateStatus, getResultMessage } from '../ui/display.js';
import { validateInputs, validateColorConfiguration } from '../ui/validation.js';
import { getColorFilterSettings, getAdditionalFilterSettings } from '../ui/events.js';
import { saveLastResults } from '../storage.js';
import { getDistributionFunction } from '../advancedRandomizer.js';

export async function randomizeCommanders(timePeriod, minRank, maxRank, quantity, colors, colorMode, numColors, selectedColorCounts, excludePartners, minCmc, maxCmc, saltMode, includeSets, excludeSets, distributionFunc = null) {
    try {
        const csvFile = CSV_FILES[timePeriod];
        if (!csvFile) {
            return {
                success: false,
                error: `Invalid time period: ${timePeriod}`
            };
        }
        
        // Load commanders
        let commanders = await loadCSV(csvFile);
        const totalLoaded = commanders.length;
        
        // Filter out partners if requested
        if (excludePartners) {
            commanders = commanders.filter(c => !c.name.includes(' // '));
        }
        
        // Build filter description
        let filterDesc = `${timePeriod} ranks ${minRank}-${maxRank}`;
        if (colors !== null || numColors !== null || (selectedColorCounts && selectedColorCounts.length > 0)) {
            if (numColors !== null) {
                filterDesc += ` with exactly ${numColors} color(s)`;
                if (colors) {
                    const modeDesc = {'exactly': 'exactly', 'including': 'including', 'atmost': 'at most'}[colorMode];
                    filterDesc += ` (${modeDesc}: ${colors})`;
                }
            } else if (selectedColorCounts && selectedColorCounts.length > 0) {
                // Multi-select color counts
                const countsStr = selectedColorCounts.sort((a, b) => a - b).join(', ');
                filterDesc += ` with ${countsStr} color(s)`;
                
                if (colors) {
                    const modeDesc = {'exactly': 'exactly', 'including': 'including', 'atmost': 'at most'}[colorMode];
                    filterDesc += ` (${modeDesc}: ${colors})`;
                }
            } else if (colors) {
                const modeDesc = {'exactly': 'exactly', 'including': 'including', 'atmost': 'at most'}[colorMode];
                filterDesc += ` with ${modeDesc} colors: ${colors}`;
            } else if (colors === '') {
                filterDesc += ' (colorless only)';
            }
        }
        
        if (excludePartners) {
            filterDesc += ' (excluding partners)';
        }
        
        // Add CMC filter to description
        if (minCmc !== null && maxCmc !== null) {
            filterDesc += `, CMC ${minCmc}-${maxCmc}`;
        }
        
        // Add salt filter to description
        if (saltMode === 'salty') {
            filterDesc += `, Salty commanders`;
        } else if (saltMode === 'chill') {
            filterDesc += `, Chill commanders`;
        }
        
        // Add set filter to description
        if (includeSets && includeSets.length > 0) {
            filterDesc += `, Include sets: ${includeSets.join(', ')}`;
        }
        if (excludeSets && excludeSets.length > 0) {
            filterDesc += `, Exclude sets: ${excludeSets.join(', ')}`;
        }
        
        // Add distribution mode to description
        if (distributionFunc) {
            filterDesc += ` (Advanced Randomizer)`;
        }
        
        // Select random commanders using weighted or uniform distribution
        const selected = distributionFunc 
            ? selectRandomCommandersWeighted(
                commanders, minRank, maxRank, quantity, colors, colorMode, numColors, selectedColorCounts, minCmc, maxCmc, saltMode, includeSets, excludeSets, distributionFunc
            )
            : selectRandomCommanders(
                commanders, minRank, maxRank, quantity, colors, colorMode, numColors, selectedColorCounts, minCmc, maxCmc, saltMode, includeSets, excludeSets
            );
        
        return {
            success: true,
            commanders: selected,
            total_available: commanders.length,
            total_loaded: totalLoaded,
            filter_description: filterDesc,
            quantity_requested: quantity,
            quantity_returned: selected.length
        };
        
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

export async function handleRandomize() {
    console.log('handleRandomize called');
    
    // Validate inputs
    const validation = validateInputs();
    if (!validation) {
        console.error('Validation failed');
        return;
    }
    
    const { minRank, maxRank, quantity } = validation;
    const timePeriod = document.getElementById('time-period').value;
    const { colors, color_mode, num_colors, selected_color_counts } = getColorFilterSettings();
    const { enable_cmc, min_cmc, max_cmc, enable_salt, salt_mode, enable_set, include_sets, exclude_sets } = getAdditionalFilterSettings();
    const excludePartners = document.getElementById('exclude-partners').checked;
    const useTextOutput = document.getElementById('text-output').checked;
    
    // Get the distribution function (returns null if not using advanced randomizer)
    const distributionFunc = getDistributionFunction();
    
    // Validate color configuration
    const colorValidation = validateColorConfiguration();
    
    console.log('Request params:', { minRank, maxRank, quantity, timePeriod, colors, color_mode, num_colors, selected_color_counts, enable_cmc, min_cmc, max_cmc, enable_salt, salt_mode, enable_set, include_sets, exclude_sets });
    
    // Clear previous results but preserve sort state
    clearResults(true);
    
    // Show loading
    updateStatus('Loading commanders...');
    document.getElementById('randomize-btn').disabled = true;
    document.getElementById('loading-indicator').classList.remove('hidden');
    
    try {
        // Call service function
        const result = await randomizeCommanders(
            timePeriod,
            minRank,
            maxRank,
            quantity,
            colors,
            color_mode,
            num_colors,
            selected_color_counts,
            excludePartners,
            min_cmc,
            max_cmc,
            salt_mode,
            include_sets,
            exclude_sets,
            distributionFunc
        );
        
        console.log('Service response:', result);
        
        if (!result.success) {
            alert(`Error: ${result.error}`);
            updateStatus(`Error: ${result.error}`);
            return;
        }
        
        const commanders = result.commanders;
        const commandersCount = commanders ? commanders.length : 0;
        
        // Generate appropriate status message
        const statusMessage = getResultMessage(result, quantity, colorValidation);
        
        // Display results
        if (commandersCount > 0) {
            if (useTextOutput) {
                // For text output, still fetch all URLs first (needed for display)
                for (const commander of commanders) {
                    commander.edhrec_url = commanderNameToUrl(commander.name);
                    commander.image_url = await getCardImageUrl(commander.name);
                }
                displayTextResults(result);
            } else {
                // For card images, display immediately and load images progressively
                displayCardImagesProgressive(commanders);
            }
            updateStatus(statusMessage);
            
            // Save the results for next visit
            saveLastResults(commanders);
        } else {
            updateStatus(statusMessage);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert(`An error occurred: ${error.message}`);
        updateStatus(`Error: ${error.message}`);
    } finally {
        document.getElementById('randomize-btn').disabled = false;
        document.getElementById('loading-indicator').classList.add('hidden');
    }
}
