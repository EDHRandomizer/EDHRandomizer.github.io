// ========================================
// CSV DATA LOADING & PARSING
// ========================================

import { CSV_FILES } from './config.js';

// Global state
export let commandersCache = {};
export let csvInfo = {};

// Load and parse CSV file
export async function loadCSV(filename) {
    if (commandersCache[filename]) {
        return commandersCache[filename];
    }
    
    try {
        const response = await fetch(filename);
        const text = await response.text();
        
        const commanders = parseCSV(text);
        commandersCache[filename] = commanders;
        return commanders;
    } catch (error) {
        console.error(`Error loading ${filename}:`, error);
        return [];
    }
}

// Parse CSV text to commander objects
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    
    const commanders = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        // Parse CSV line (handle quoted fields)
        const values = parseCSVLine(line);
        
        if (values.length < headers.length) continue;
        
        const row = {};
        headers.forEach((header, index) => {
            row[header] = values[index] || '';
        });
        
        // Skip undefined rows
        if (row['Rank'] === 'undefined' || row['Name'] === 'undefined') {
            continue;
        }
        
        try {
            const rank = parseInt(row['Rank']);
            if (isNaN(rank)) continue;
            
            commanders.push({
                rank: rank,
                name: row['Name'],
                colors: row['Colors'] || '',
                cmc: row['CMC'] || '',
                rarity: row['Rarity'] || '',
                type: row['Type'] || '',
                salt: row['Salt'] || '',
                set_code: row['Set Code'] || '',
                set_name: row['Set Name'] || ''
            });
        } catch (e) {
            continue;
        }
    }
    
    return commanders;
}

// Parse a single CSV line handling quoted fields
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim().replace(/^"|"$/g, ''));
            current = '';
        } else {
            current += char;
        }
    }
    
    values.push(current.trim().replace(/^"|"$/g, ''));
    return values;
}

// Get CSV info for all time periods
export async function getCsvInfo() {
    const info = {};
    
    for (const [period, csvFile] of Object.entries(CSV_FILES)) {
        try {
            const commanders = await loadCSV(csvFile);
            const maxRank = commanders.length > 0 ? Math.max(...commanders.map(c => c.rank)) : 0;
            
            info[period] = {
                file: csvFile,
                max_rank: maxRank,
                count: commanders.length
            };
        } catch (error) {
            info[period] = {
                file: csvFile,
                max_rank: 0,
                count: 0,
                error: error.message
            };
        }
    }
    
    csvInfo = info;
    return info;
}
