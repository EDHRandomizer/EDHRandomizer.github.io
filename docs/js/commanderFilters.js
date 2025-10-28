// ========================================
// COMMANDER FILTERING LOGIC
// ========================================

// Helper: Check if two sets are equal
function areSetsEqual(set1, set2) {
    if (set1.size !== set2.size) return false;
    for (const item of set1) {
        if (!set2.has(item)) return false;
    }
    return true;
}

// Helper: Check if set1 is a subset of set2
function isSubset(set1, set2) {
    for (const item of set1) {
        if (!set2.has(item)) return false;
    }
    return true;
}

export function filterByColors(commanders, colors, mode, numColors = null, selectedColorCounts = null) {
    // First filter by number of colors if specified
    if (numColors !== null) {
        // Exact number of colors (simple mode)
        commanders = commanders.filter(commander => {
            const commanderColorCount = commander.colors.replace(/,/g, '').replace(/ /g, '').length;
            return commanderColorCount === numColors;
        });
        
        // If we only want colorless (0 colors) and no specific colors selected, return now
        if (numColors === 0) {
            return commanders;
        }
    } else if (selectedColorCounts && selectedColorCounts.length > 0) {
        // Multi-select color counts (advanced mode)
        commanders = commanders.filter(commander => {
            const commanderColorCount = commander.colors.replace(/,/g, '').replace(/ /g, '').length;
            return selectedColorCounts.includes(commanderColorCount);
        });
        
        // If only colorless selected and no specific colors, return now
        if (selectedColorCounts.length === 1 && selectedColorCounts[0] === 0) {
            return commanders;
        }
        // If colorless is among multiple selections and no colors specified, include colorless
        if ((colors === null || colors === '' || colors === undefined) && selectedColorCounts.includes(0)) {
            return commanders;
        }
    }
    
    // If no colors specified and no color count filter, return all commanders
    if (colors === '' || colors === null || colors === undefined) {
        // Special case: if mode is "exactly" and no colors selected, return colorless
        if (mode === 'exactly' && (numColors === null || numColors === undefined) && 
            (!selectedColorCounts || selectedColorCounts.length === 0)) {
            return commanders.filter(c => c.colors === '');
        }
        // Already filtered by color count if applicable
        return commanders;
    }
    
    // Parse the color set
    const filterColors = new Set(colors.toUpperCase().replace(/,/g, '').replace(/ /g, '').split(''));
    
    // If no colors specified but numColors was used, we already filtered
    if (filterColors.size === 0) {
        return commanders;
    }
    
    const filtered = [];
    for (const commander of commanders) {
        const commanderColors = new Set(commander.colors.replace(/,/g, '').replace(/ /g, '').split(''));
        
        if (mode === 'exactly') {
            // Commander must have exactly these colors (no more, no less)
            if (areSetsEqual(commanderColors, filterColors)) {
                filtered.push(commander);
            }
        } else if (mode === 'including') {
            // Commander must include all specified colors (can have more)
            if (isSubset(filterColors, commanderColors)) {
                filtered.push(commander);
            }
        } else if (mode === 'atmost') {
            // Commander can only use colors from the specified set (subset or equal)
            if (isSubset(commanderColors, filterColors)) {
                filtered.push(commander);
            }
        }
    }
    
    return filtered;
}

// Select random commanders
export function selectRandomCommanders(
    commanders,
    minRank,
    maxRank,
    quantity, 
    colors = null, 
    colorMode = 'exactly',
    numColors = null,
    selectedColorCounts = null,
    minCmc = null,
    maxCmc = null,
    saltMode = null
) {
    // Filter commanders by rank range
    let filtered = commanders.filter(c => c.rank >= minRank && c.rank <= maxRank);
    
    // Apply color filter if specified
    if (colors !== null || numColors !== null || selectedColorCounts !== null) {
        filtered = filterByColors(filtered, colors, colorMode, numColors, selectedColorCounts);
    }
    
    // Apply CMC filter if specified
    if (minCmc !== null || maxCmc !== null) {
        filtered = filtered.filter(commander => {
            const cmc = parseInt(commander.cmc);
            if (isNaN(cmc)) return false;
            if (minCmc !== null && cmc < minCmc) return false;
            if (maxCmc !== null && cmc > maxCmc) return false;
            return true;
        });
    }
    
    // Apply salt filter if specified
    // 'salty' = commanders with salt > 0.8 (top ~5% saltiest)
    // 'chill' = commanders with salt <= 0.8 (bottom ~95%)
    if (saltMode !== null) {
        filtered = filtered.filter(commander => {
            const salt = parseFloat(commander.salt);
            if (isNaN(salt)) return false;
            
            if (saltMode === 'salty') {
                return salt > 0.8;
            } else if (saltMode === 'chill') {
                return salt <= 0.8;
            }
            return true;
        });
    }
    
    if (filtered.length === 0) {
        console.log(`No commanders found in rank range ${minRank}-${maxRank} with the specified color filter`);
        return [];
    }
    
    if (quantity > filtered.length) {
        console.log(`Warning: Only ${filtered.length} commanders available with current filters`);
        console.log(`Returning all ${filtered.length} commanders instead of ${quantity}`);
        quantity = filtered.length;
    }
    
    // Randomly select the specified quantity
    const selected = [];
    const available = [...filtered];
    
    for (let i = 0; i < quantity; i++) {
        const randomIndex = Math.floor(Math.random() * available.length);
        selected.push(available[randomIndex]);
        available.splice(randomIndex, 1);
    }
    
    return selected;
}

/**
 * Select random commanders using weighted probability distribution
 * @param {Array} commanders - Array of commander objects with rank property
 * @param {number} minRank - Minimum rank in range
 * @param {number} maxRank - Maximum rank in range
 * @param {number} quantity - Number of commanders to select
 * @param {string|null} colors - Color filter string
 * @param {string} colorMode - Color filter mode
 * @param {number|null} numColors - Number of colors filter
 * @param {Array|null} selectedColorCounts - Selected color counts
 * @param {number|null} minCmc - Minimum CMC
 * @param {number|null} maxCmc - Maximum CMC
 * @param {string|null} saltMode - Salt filter mode
 * @param {Function|null} distributionFunc - Probability distribution function (rank, min, max) => weight
 * @returns {Array} - Array of selected commanders
 */
export function selectRandomCommandersWeighted(
    commanders,
    minRank,
    maxRank,
    quantity,
    colors = null,
    colorMode = 'exactly',
    numColors = null,
    selectedColorCounts = null,
    minCmc = null,
    maxCmc = null,
    saltMode = null,
    distributionFunc = null
) {
    // Filter commanders by rank range
    let filtered = commanders.filter(c => c.rank >= minRank && c.rank <= maxRank);
    
    // Apply color filter if specified
    if (colors !== null || numColors !== null || selectedColorCounts !== null) {
        filtered = filterByColors(filtered, colors, colorMode, numColors, selectedColorCounts);
    }
    
    // Apply CMC filter if specified
    if (minCmc !== null || maxCmc !== null) {
        filtered = filtered.filter(commander => {
            const cmc = parseInt(commander.cmc);
            if (isNaN(cmc)) return false;
            if (minCmc !== null && cmc < minCmc) return false;
            if (maxCmc !== null && cmc > maxCmc) return false;
            return true;
        });
    }
    
    // Apply salt filter if specified
    if (saltMode !== null) {
        filtered = filtered.filter(commander => {
            const salt = parseFloat(commander.salt);
            if (isNaN(salt)) return false;
            
            if (saltMode === 'salty') {
                return salt > 0.8;
            } else if (saltMode === 'chill') {
                return salt <= 0.8;
            }
            return true;
        });
    }
    
    if (filtered.length === 0) {
        console.log(`No commanders found in rank range ${minRank}-${maxRank} with the specified filters`);
        return [];
    }
    
    if (quantity > filtered.length) {
        console.log(`Warning: Only ${filtered.length} commanders available with current filters`);
        console.log(`Returning all ${filtered.length} commanders instead of ${quantity}`);
        quantity = filtered.length;
    }
    
    // If no distribution function provided, use uniform distribution
    if (!distributionFunc) {
        return selectRandomCommanders(
            commanders, minRank, maxRank, quantity, colors, colorMode,
            numColors, selectedColorCounts, minCmc, maxCmc, saltMode
        );
    }
    
    console.log('🎲 Using weighted distribution with range:', minRank, '-', maxRank);
    
    // Calculate weights for each commander
    const commandersWithWeights = filtered.map(commander => {
        const weight = distributionFunc(commander.rank, minRank, maxRank);
        // Ensure weight is positive and finite
        const finalWeight = (!isFinite(weight) || weight < 0) ? 0 : weight;
        return {
            commander,
            weight: finalWeight,
            rawWeight: weight  // Keep raw weight for debugging
        };
    });
    
    // Check if any weights are Infinity
    const hasInfinityWeights = commandersWithWeights.some(c => !isFinite(c.rawWeight) && c.rawWeight > 0);
    if (hasInfinityWeights) {
        console.warn('⚠️ Some weights are Infinity - equation produces numbers too large for JavaScript to handle');
        console.warn('This will cause unexpected behavior. Try using smaller exponents (e.g., ** 2 or ** 3 instead of ** 1000)');
        alert('Warning: Your equation produces numbers too large (Infinity).\n\nThis happens with very large exponents like ** 1000.\n\nTry using smaller exponents (e.g., ** 2, ** 3, ** 5) for better results.');
    }
    
    // Log first few weights for debugging
    console.log('Sample weights:', commandersWithWeights.slice(0, 5).map(c => ({
        rank: c.commander.rank,
        name: c.commander.name,
        weight: c.weight
    })));
    
    // Calculate total weight
    const totalWeight = commandersWithWeights.reduce((sum, item) => sum + item.weight, 0);
    
    if (totalWeight === 0) {
        console.error('Total weight is 0, falling back to uniform distribution');
        return selectRandomCommanders(
            commanders, minRank, maxRank, quantity, colors, colorMode,
            numColors, selectedColorCounts, minCmc, maxCmc, saltMode
        );
    }
    
    // Select commanders using weighted random selection
    const selected = [];
    const available = [...commandersWithWeights];
    
    for (let i = 0; i < quantity; i++) {
        // Calculate cumulative weights
        let cumulativeWeight = 0;
        const cumulativeWeights = available.map(item => {
            cumulativeWeight += item.weight;
            return cumulativeWeight;
        });
        
        // Generate random number between 0 and total weight
        const randomValue = Math.random() * cumulativeWeight;
        
        // Find the selected commander
        let selectedIndex = 0;
        for (let j = 0; j < cumulativeWeights.length; j++) {
            if (randomValue <= cumulativeWeights[j]) {
                selectedIndex = j;
                break;
            }
        }
        
        // Add to selected and remove from available
        selected.push(available[selectedIndex].commander);
        available.splice(selectedIndex, 1);
    }
    
    return selected;
}
