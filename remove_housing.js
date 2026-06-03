const fs = require('fs');
const { parser } = require('stream-json');
const { streamArray } = require('stream-json/streamers/StreamArray');
const { chain } = require('stream-chain');

const inputFile = 'data_20260603.json';
const tempFile = 'data_20260603_tmp.json';

console.log(`Aloitetaan suodatus RAM-ystävällisesti (Node.js): ${inputFile}`);

let processed = 0;
let removed = 0;
let first = true;

const terms = ["asunto oy", "asunto-osakeyhtiö", "kiinteistö oy", "kiinteistöosakeyhtiö", "as.oy", "as. oy", "asunto-oy"];

const pipeline = chain([
  fs.createReadStream(inputFile),
  parser(),
  streamArray(),
  data => {
    processed++;
    if (processed % 100000 === 0) {
      console.log(`Käsitelty ${processed} yritystä, poistettu asunto/kiinteistö-yhtiöitä tähän mennessä ${removed}...`);
    }

    const company = data.value;
    const names = company.names || [];
    const companyName = names.length > 0 ? (names[0].name || '') : '';
    const nameLower = companyName.toLowerCase();
    
    const mbl = company.mainBusinessLine;
    let industryCode = '';
    if (mbl && typeof mbl === 'object') {
        industryCode = mbl.type || '';
    } else if (typeof mbl === 'string') {
        industryCode = mbl;
    }
    
    let isHousing = false;
    for (const term of terms) {
      if (nameLower.includes(term)) {
        isHousing = true;
        break;
      }
    }
    
    if (!isHousing && industryCode.startsWith("682")) {
      isHousing = true;
    }
    
    if (isHousing) {
      removed++;
      return null;
    }
    return company;
  }
]);

const out = fs.createWriteStream(tempFile);
out.write('[\n');

pipeline.on('data', company => {
  if (!first) {
    out.write(',\n');
  }
  first = false;
  out.write(JSON.stringify(company));
});

pipeline.on('end', () => {
  out.write('\n]\n');
  out.end();
});

out.on('finish', () => {
  console.log(`\nSuodatus valmis!`);
  console.log(`Käsitelty yhteensä: ${processed} yritystä.`);
  console.log(`Poistettu lopullisesti: ${removed} asunto/kiinteistöyhtiötä.`);
  console.log(`Korvataan alkuperäinen tiedosto...`);
  
  fs.renameSync(tempFile, inputFile);
  console.log(`Tiedosto korvattu onnistuneesti! Voit poistaa remove_housing.js ja remove_housing.py tiedostot.`);
});

pipeline.on('error', (err) => {
  console.error('Virhe suodatuksessa:', err);
});
