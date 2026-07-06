import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = "https://crnhghkopqputqekbmid.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_uqYjWYc7tDT7w56tMiwisQ_hedNFgW5";
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function test() {
  const startDate = "2026-06-29T00:00:00Z";
  const endDate = "2026-07-06T23:59:59Z";

  console.log("Querying historical_data...");
  const { data: hist, error: histErr } = await supabase
    .from('historical_data')
    .select('timestamp, consumption')
    .gte('timestamp', startDate)
    .lte('timestamp', endDate)
    .order('timestamp', { ascending: true });

  if (histErr) console.error("Hist Error:", histErr);
  else console.log(`Hist count: ${hist?.length}, First:`, hist?.[0], "Last:", hist?.[hist?.length - 1]);

  const tables = ['predictions_rte', 'predictions_timesfm', 'predictions_naive', 'predictions_lightgbm'];

  for (const table of tables) {
    console.log(`Querying ${table}...`);
    const { data, error } = await supabase
      .from(table)
      .select('*')
      .gte('timestamp', startDate)
      .lte('timestamp', endDate)
      .order('timestamp', { ascending: true });

    if (error) console.error(`${table} Error:`, error);
    else console.log(`${table} count: ${data?.length}, First:`, data?.[0], "Last:", data?.[data?.length - 1]);
  }
}

test();
