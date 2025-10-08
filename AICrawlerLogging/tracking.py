import Pandas
import NumPY
import MatPlotlib

server_df = pd.read_csv("server_logs.csv")
bots_df = pd.read_csv("bots_table.csv")

server_df['Date'] = pd.to_datetime(server_df['Date'])
bots_df['Date'] = pd.to_datetime(bots_df['Date'])
bots_df['Last hit date'] = pd.to_datetime(bots_df['Last hit date'])

# server_df["Page path"]
# bots_df["Page path"]

merged = pd.merge(server_df, bots_df, on=["Date", "Page path"], how="left")
merged["Page path"].head(30)
merged = merged[merged["Bot"].notna() & (merged["Bot"] != "Unknown") & (merged["Page path"] != "/") & (merged["Page path"] != "/blank")]
merged.dropna()
