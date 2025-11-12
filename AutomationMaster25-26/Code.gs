function autoUpdateFromMaster() {
  try {
    // === CONFIGURATION ===
    const MASTER_SHEET_ID = '1DxqkCyUOV8IJGfY6wu0p_TXl5yR_wqBVh_LrXl5p0Bw'; // master sheet
    const MASTER_TAB_NAME = 'sales data'; // master tab
    const TARGET_SHEET_ID = '1GLKQllVmysW4ARvx7RWs2KDQOmsnNMwJWaqebFsMqs4'; // target sheet
    const TARGET_TAB_NAME = 'Sheet1'; // target tab

    // === OPEN SHEETS ===
    const masterSheet = SpreadsheetApp.openById(MASTER_SHEET_ID).getSheetByName(MASTER_TAB_NAME);
    const targetSheet = SpreadsheetApp.openById(TARGET_SHEET_ID).getSheetByName(TARGET_TAB_NAME);

    // === READ MASTER DATA ===
    const data = masterSheet.getDataRange().getValues();
    const header = data[0];
    const catIndex = header.indexOf('category');
    const valIndex = header.indexOf('order_value_EUR');

    if (catIndex === -1 || valIndex === -1)
      throw new Error('Required columns not found (category / order_value_EUR).');

    // === AGGREGATE TOTALS BY CATEGORY ===
    const totals = {};
    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      const cat = String(row[catIndex]).trim();
      const val = parseFloat(row[valIndex]) || 0;
      if (cat) totals[cat] = (totals[cat] || 0) + val;
    }

    // === READ TARGET SHEET ===
    const targetData = targetSheet.getDataRange().getValues();
    const categories = targetData.slice(1).map(r => String(r[0]).trim());
    const lastHeader = targetData[0][targetData[0].length - 1];

    // === CHECK DUPLICATION ===
    const now = new Date();
    const newHeader = Utilities.formatDate(now, 'Asia/Kolkata', 'MMM dd, yyyy HH:mm');
    if (newHeader === lastHeader) {
      Logger.log('⚠️ Duplicate timestamp detected — skipping update.');
      return;
    }

    // === ADD NEW COLUMN HEADER ===
    const newCol = targetData[0].length + 1;
    targetSheet.getRange(1, newCol).setValue(newHeader);

    // === UPDATE VALUES ===
    const newValues = categories.map(cat => [totals[cat] || '']);
    targetSheet.getRange(2, newCol, newValues.length, 1).setValues(newValues);

    Logger.log(`✅ Updated ${newValues.length} rows for ${newHeader}`);
  } catch (err) {
    Logger.log('❌ Script failed: ' + err.message);
  }
}
