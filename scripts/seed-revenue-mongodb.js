#!/usr/bin/env node

const { MongoClient } = require('mongodb');
const fs = require('fs');
const path = require('path');

const MONGODB_URL = process.env.MONGODB_URL || process.env.MONGODB_URI || 'mongodb+srv://alreadyherellc_db_user:Alr3adyh3r3@profitenginev5.4ccsjgp.mongodb.net/?appName=ProfitEnginev5';
const DB_NAME = process.env.MONGODB_DB || 'profitenginev5';

async function seedRevenueData() {
  const client = new MongoClient(MONGODB_URL);
  
  try {
    console.log('Connecting to MongoDB...');
    await client.connect();
    const db = client.db(DB_NAME);
    
    // Get transaction files
    const runtimeDir = path.join(process.cwd(), '.runtime', 'revenue');
    const txFile = path.join(runtimeDir, 'transactions.jsonl');
    const sampleFile = path.join(runtimeDir, 'sample_data.jsonl');
    
    const collection = db.collection('revenue_transactions');
    
    // Create index on date for performance
    await collection.createIndex({ date: 1 });
    await collection.createIndex({ channel: 1, date: 1 });
    
    let imported = 0;
    
    // Import real transactions
    if (fs.existsSync(txFile)) {
      console.log(`Reading transactions from ${txFile}...`);
      const lines = fs.readFileSync(txFile, 'utf8').split('\n').filter(l => l.trim());
      
      for (const line of lines) {
        try {
          const tx = JSON.parse(line);
          const date = new Date(tx.timestamp);
          const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
          
          const doc = {
            ...tx,
            date: dateStr,
            imported_at: new Date(),
          };
          
          await collection.updateOne(
            { source_id: tx.source_id },
            { $set: doc },
            { upsert: true }
          );
          imported++;
        } catch (e) {
          console.error(`Failed to import line: ${line}`, e.message);
        }
      }
    }
    
    // Import sample data
    if (fs.existsSync(sampleFile)) {
      console.log(`Reading sample data from ${sampleFile}...`);
      const lines = fs.readFileSync(sampleFile, 'utf8').split('\n').filter(l => l.trim());
      
      for (const line of lines) {
        try {
          const tx = JSON.parse(line);
          const date = new Date(tx.timestamp);
          const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
          
          const doc = {
            ...tx,
            date: dateStr,
            imported_at: new Date(),
          };
          
          await collection.updateOne(
            { source_id: tx.source_id },
            { $set: doc },
            { upsert: true }
          );
          imported++;
        } catch (e) {
          console.error(`Failed to import sample line: ${line}`, e.message);
        }
      }
    }
    
    console.log(`\n✅ Imported ${imported} transactions to MongoDB`);
    
    // Show summary
    const summary = await collection.aggregate([
      {
        $group: {
          _id: '$channel',
          count: { $sum: 1 },
          total: { $sum: '$amount_usd' }
        }
      },
      { $sort: { total: -1 } }
    ]).toArray();
    
    console.log('\nRevenue Summary by Channel:');
    console.log('============================');
    let grandTotal = 0;
    for (const row of summary) {
      console.log(`${row._id.padEnd(15)} | ${row.count.toString().padStart(3)} tx | $${row.total.toFixed(2).padStart(8)}`);
      grandTotal += row.total;
    }
    console.log('----');
    console.log(`${'TOTAL'.padEnd(15)} | ${summary.reduce((a, b) => a + b.count, 0).toString().padStart(3)} tx | $${grandTotal.toFixed(2).padStart(8)}`);
    
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  } finally {
    await client.close();
    console.log('\nMongoDB connection closed');
  }
}

seedRevenueData();
