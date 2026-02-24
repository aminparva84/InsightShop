# Install C++ Build Tools for ChromaDB

ChromaDB's `chroma-hnswlib` needs Microsoft Visual C++ 14.0+ to compile. Use one of the options below.

---

## Option A: winget (recommended)

**Run PowerShell or Terminal as Administrator**, then:

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --source winget --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" --accept-package-agreements --accept-source-agreements
```

- First download is ~1.5 MB (bootstrapper), then the installer downloads the C++ workload (several hundred MB). Keep the window open until it finishes.
- If you see "WinHttpSendRequest: 12002" or "0x80072ee2", the download timed out — try again when the connection is stable.
- Exit code **3010** means success but **reboot required**; restart the PC, then install ChromaDB.

After installation (and reboot if prompted), install ChromaDB:

```powershell
cd c:\code\InsightShop
pip install chromadb==0.4.18
```

---

## Option B: Manual download

1. Open: **https://visualstudio.microsoft.com/visual-cpp-build-tools/**
2. Click **"Download Build Tools"** and run the downloaded `vs_BuildTools.exe`.
3. In the installer, select **"Desktop development with C++"** (or at least **MSVC** and **Windows SDK**).
4. Click **Install** and wait for it to finish. Reboot if asked.
5. Then in a terminal:
   ```powershell
   cd c:\code\InsightShop
   pip install chromadb==0.4.18
   ```

---

## After ChromaDB is installed

1. In **Admin → Products**, click **"Sync to AI Search"** to index products for semantic search.
2. The AI assistant will then use both keyword/search and vector (semantic) search.
