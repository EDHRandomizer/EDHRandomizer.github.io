function normalizeName(name) {
    // Remove commas
    name = name.replace(/,/g, '');
    
    // Remove apostrophes
    name = name.replace(/'/g, '');
    
    // Remove quotes
    name = name.replace(/"/g, '');
    
    // Remove periods (THIS IS MISSING!)
    name = name.replace(/\./g, '');
    
    // Normalize unicode characters
    name = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    
    // Replace spaces with hyphens
    name = name.replace(/ /g, '-');
    
    // Convert to lowercase
    name = name.toLowerCase();
    
    return name;
}

function commanderNameToUrl(name) {
    if (name.includes('//')) {
        const parts = name.split('//');
        const convertedParts = parts.map(part => normalizeName(part.trim()));
        const slug = convertedParts.join('-');
        return `https://edhrec.com/commanders/${slug}`;
    } else {
        const slug = normalizeName(name);
        return `https://edhrec.com/commanders/${slug}`;
    }
}

console.log('Test: Mr. Orfeo, the Boulder');
console.log('Result:', commanderNameToUrl('Mr. Orfeo, the Boulder'));
console.log('Expected: https://edhrec.com/commanders/mr-orfeo-the-boulder');