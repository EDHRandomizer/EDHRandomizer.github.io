// ========================================
// ADVANCED PROBABILITY DISTRIBUTION FUNCTIONS
// ========================================

/**
 * Parse a user-provided math equation string into a probability function
 * Variables available: rank, min, max
 * @param {string} equation - User's math equation (e.g., "max - rank", "(max - rank) / (max - min)")
 * @param {number} minRank - Minimum rank to test with
 * @param {number} maxRank - Maximum rank to test with
 * @returns {Function|null} - A function that takes (rank, min, max) and returns a weight, or null if invalid
 */
export function parseDistributionEquation(equation, minRank = 600, maxRank = 1400) {
    if (!equation || typeof equation !== 'string') {
        return null;
    }
    
    // Sanitize the equation - only allow safe characters
    const sanitized = equation.trim();
    const allowedPattern = /^[0-9+\-*/().\s,?:><!=&|eaMthxpowsqrtlognbcdfijkuvyzRankMinMax]+$/i;
    
    if (!allowedPattern.test(sanitized)) {
        console.error('Invalid characters in equation. Only numbers, operators, Math functions, and variables (rank, min, max) are allowed.');
        return null;
    }
    
    // Replace variable names with parameter references
    // Use word boundaries to avoid partial matches
    let functionBody = sanitized
        .replace(/\brank\b/gi, 'rank')
        .replace(/\bmin\b/gi, 'min')
        .replace(/\bmax\b/gi, 'max');
    
    try {
        // Create the function
        const func = new Function('rank', 'min', 'max', `return ${functionBody};`);
        
        // Test with the actual min/max values from settings
        const testMid = func((minRank + maxRank) / 2, minRank, maxRank);
        const testMin = func(minRank, minRank, maxRank);
        const testMax = func(maxRank, minRank, maxRank);
        
        // Only reject if we get NaN (actual error), allow Infinity (just means very large exponent)
        if (isNaN(testMid) || isNaN(testMin) || isNaN(testMax)) {
            console.error('Equation produces NaN (invalid math) with range', minRank, '-', maxRank);
            return null;
        }
        
        // Warn about Infinity but still allow it
        if (!isFinite(testMid) || !isFinite(testMin) || !isFinite(testMax)) {
            console.warn('⚠️ Equation produces Infinity - exponent may be too large. Results may be unpredictable.');
        }
        
        return func;
    } catch (error) {
        console.error('Error parsing equation:', error);
        return null;
    }
}

/**
 * Preset distribution functions
 */
export const DISTRIBUTION_PRESETS = {
    uniform: {
        name: 'Uniform [Default]',
        description: 'All commanders equally likely',
        equation: '1',
        func: (rank, min, max) => 1
    },
    favorPopular: {
        name: 'Favor Popular',
        description: 'Lower rank numbers (more popular) are more likely - linear from 100 at min to 50 at max',
        equation: '100 - (rank - min) * 50 / (max - min)',
        func: (rank, min, max) => {
            // Linear decline from 100 at min rank to 50 at max rank
            return 100 - ((rank - min) * 50 / (max - min));
        }
    },
    favorObscure: {
        name: 'Favor Obscure',
        description: 'Higher rank numbers (less popular) are more likely - linear from 50 at min to 100 at max',
        equation: '50 + (rank - min) * 50 / (max - min)',
        func: (rank, min, max) => {
            // Linear increase from 50 at min rank to 100 at max rank
            return 50 + ((rank - min) * 50 / (max - min));
        }
    },
    stronglyPopular: {
        name: 'Strongly Popular',
        description: 'Strongly favor lower rank numbers (most popular)',
        equation: '(max - rank) ** 2',
        func: (rank, min, max) => Math.pow(max - rank, 2)
    },
    stronglyObscure: {
        name: 'Strongly Obscure',
        description: 'Strongly favor higher rank numbers (most obscure)',
        equation: '(rank - min) ** 2',
        func: (rank, min, max) => Math.pow(rank - min, 2)
    },
    normal: {
        name: 'Normal Distribution',
        description: 'Bell curve centered at rank 1100 with fixed width - most selections near rank 1100',
        equation: 'Math.exp(-((rank - 1100) ** 2) / (2 * 300 ** 2))',
        func: (rank, min, max) => {
            const mean = 1100;  // Fixed center at rank 1100
            const sigma = 300;  // Fixed standard deviation - controls bell width
            const exponent = -Math.pow(rank - mean, 2) / (2 * Math.pow(sigma, 2));
            return Math.exp(exponent);
        }
    }
};

/**
 * Get the distribution function based on current UI settings
 * @returns {Function|null} - Distribution function or null for uniform distribution
 */
export function getDistributionFunction() {
    const enabled = document.getElementById('enable-advanced-randomizer')?.checked;
    
    if (!enabled) {
        return null; // Use uniform distribution
    }
    
    const equation = document.getElementById('distribution-equation')?.value;
    
    if (!equation || equation.trim() === '') {
        console.warn('Advanced randomizer enabled but no equation provided');
        return null;
    }
    
    // Get the actual min/max from settings to validate with
    const minRank = parseInt(document.getElementById('min-rank')?.value) || 1;
    const maxRank = parseInt(document.getElementById('max-rank')?.value) || 1000;
    
    const parsedFunc = parseDistributionEquation(equation, minRank, maxRank);
    if (!parsedFunc) {
        console.error('Failed to parse equation, falling back to uniform distribution');
        return null;
    }
    
    return parsedFunc;
}

/**
 * Set the equation in the input field
 * @param {string} equation - The equation to set
 */
export function setEquation(equation) {
    const input = document.getElementById('distribution-equation');
    if (input) {
        input.value = equation;
        // Trigger change event to save settings
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
}
