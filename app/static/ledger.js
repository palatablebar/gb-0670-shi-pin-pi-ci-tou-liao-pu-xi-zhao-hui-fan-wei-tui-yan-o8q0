document.querySelectorAll('.filter').forEach(input=>{input.addEventListener('input',()=>{const table=input.closest('.panel').querySelector('table');for(const row of table.tBodies[0].rows)row.hidden=!row.textContent.toLowerCase().includes(input.value.toLowerCase());});});
document.querySelectorAll('.ledger td').forEach(cell=>{if(!cell.title)cell.title=cell.textContent.trim();});
