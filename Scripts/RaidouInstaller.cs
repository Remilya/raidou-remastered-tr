using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

namespace RaidouTurkishInstaller
{
    public class MainForm : Form
    {
        private TextBox txtGamePath;
        private Button btnBrowse;
        private Button btnInstall;
        private Button btnUninstall;
        private Label lblStatusBadge;
        private Label lblProgressInfo;
        private ProgressBar progressBar;
        private RichTextBox txtLog;
        private CheckBox chkSteamDeckInfo;

        private readonly string patchRootDir;

        public MainForm()
        {
            patchRootDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
            InitializeComponents();
            AutoDetectGamePath();
        }

        private void InitializeComponents()
        {
            this.Text = "RAIDOU Remastered - Türkçe Yama Kurulum Aracı";
            this.Size = new Size(680, 520);
            this.MinimumSize = new Size(680, 520);
            this.MaximumSize = new Size(680, 520);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(20, 20, 26);
            this.ForeColor = Color.FromArgb(235, 235, 240);
            this.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);

            // Header Panel
            Panel headerPanel = new Panel
            {
                Dock = DockStyle.Top,
                Height = 90,
                BackColor = Color.FromArgb(30, 22, 32)
            };
            headerPanel.Paint += (s, e) =>
            {
                using (LinearGradientBrush brush = new LinearGradientBrush(
                    headerPanel.ClientRectangle,
                    Color.FromArgb(48, 18, 28),
                    Color.FromArgb(22, 20, 30),
                    LinearGradientMode.Horizontal))
                {
                    e.Graphics.FillRectangle(brush, headerPanel.ClientRectangle);
                }
                using (Pen borderPen = new Pen(Color.FromArgb(180, 140, 65), 2))
                {
                    e.Graphics.DrawLine(borderPen, 0, headerPanel.Height - 1, headerPanel.Width, headerPanel.Height - 1);
                }
            };

            Label lblTitle = new Label
            {
                Text = "RAIDOU REMASTERED",
                Font = new Font("Segoe UI", 18f, FontStyle.Bold),
                ForeColor = Color.FromArgb(230, 190, 95),
                BackColor = Color.Transparent,
                AutoSize = true,
                Location = new Point(22, 16)
            };

            Label lblSubTitle = new Label
            {
                Text = "The Mystery of the Soulless Army — Türkçe Yama Hızlı Kurulum & Kaldırma",
                Font = new Font("Segoe UI", 9.5f, FontStyle.Regular),
                ForeColor = Color.FromArgb(200, 200, 210),
                BackColor = Color.Transparent,
                AutoSize = true,
                Location = new Point(24, 52)
            };

            lblStatusBadge = new Label
            {
                Text = "Durum Kontrol Ediliyor...",
                Font = new Font("Segoe UI", 9f, FontStyle.Bold),
                ForeColor = Color.FromArgb(255, 215, 100),
                BackColor = Color.FromArgb(45, 35, 50),
                AutoSize = false,
                Size = new Size(165, 28),
                TextAlign = ContentAlignment.MiddleCenter,
                Location = new Point(480, 30)
            };

            headerPanel.Controls.Add(lblTitle);
            headerPanel.Controls.Add(lblSubTitle);
            headerPanel.Controls.Add(lblStatusBadge);
            this.Controls.Add(headerPanel);

            // Game Directory Section
            Label lblDirTitle = new Label
            {
                Text = "Oyun Klasörü (Raidou.exe'nin bulunduğu ana klasör):",
                Font = new Font("Segoe UI", 9.5f, FontStyle.Bold),
                ForeColor = Color.FromArgb(220, 220, 230),
                Location = new Point(24, 108),
                AutoSize = true
            };
            this.Controls.Add(lblDirTitle);

            txtGamePath = new TextBox
            {
                Location = new Point(24, 134),
                Size = new Size(510, 29),
                Font = new Font("Segoe UI", 10f),
                BackColor = Color.FromArgb(32, 32, 40),
                ForeColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle
            };
            txtGamePath.TextChanged += (s, e) => UpdatePatchStatus();
            this.Controls.Add(txtGamePath);

            btnBrowse = new Button
            {
                Text = "Gözat...",
                Location = new Point(544, 132),
                Size = new Size(98, 29),
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(52, 52, 66),
                ForeColor = Color.White,
                Cursor = Cursors.Hand
            };
            btnBrowse.FlatAppearance.BorderColor = Color.FromArgb(90, 90, 110);
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            // Action Buttons
            btnInstall = new Button
            {
                Text = "TÜRKÇE YAMAYI KUR",
                Location = new Point(24, 178),
                Size = new Size(395, 46),
                Font = new Font("Segoe UI", 11.5f, FontStyle.Bold),
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(165, 38, 48),
                ForeColor = Color.White,
                Cursor = Cursors.Hand
            };
            btnInstall.FlatAppearance.BorderColor = Color.FromArgb(220, 175, 85);
            btnInstall.FlatAppearance.BorderSize = 1;
            btnInstall.Click += async (s, e) => await InstallPatchAsync();
            this.Controls.Add(btnInstall);

            btnUninstall = new Button
            {
                Text = "YAMAYI KALDIR",
                Location = new Point(432, 178),
                Size = new Size(210, 46),
                Font = new Font("Segoe UI", 10.5f, FontStyle.Bold),
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(48, 48, 60),
                ForeColor = Color.FromArgb(230, 230, 235),
                Cursor = Cursors.Hand
            };
            btnUninstall.FlatAppearance.BorderColor = Color.FromArgb(95, 95, 115);
            btnUninstall.Click += BtnUninstall_Click;
            this.Controls.Add(btnUninstall);

            // Progress Section
            lblProgressInfo = new Label
            {
                Text = "Kurulum için hazır.",
                Location = new Point(24, 236),
                Size = new Size(618, 20),
                ForeColor = Color.FromArgb(185, 185, 200)
            };
            this.Controls.Add(lblProgressInfo);

            progressBar = new ProgressBar
            {
                Location = new Point(24, 259),
                Size = new Size(618, 18),
                Style = ProgressBarStyle.Continuous
            };
            this.Controls.Add(progressBar);

            // Log Box
            txtLog = new RichTextBox
            {
                Location = new Point(24, 290),
                Size = new Size(618, 145),
                BackColor = Color.FromArgb(14, 14, 18),
                ForeColor = Color.FromArgb(200, 210, 220),
                Font = new Font("Consolas", 9f),
                ReadOnly = true,
                BorderStyle = BorderStyle.FixedSingle
            };
            this.Controls.Add(txtLog);

            // Footer Note
            Label lblFooter = new Label
            {
                Text = "Not: Yama orijinal oyun dosyalarını bozmaz (update klasörü ve version.dll üzerinden güvenli yükleme yapar).",
                Location = new Point(24, 446),
                Size = new Size(618, 22),
                Font = new Font("Segoe UI", 8.5f, FontStyle.Italic),
                ForeColor = Color.FromArgb(150, 150, 165)
            };
            this.Controls.Add(lblFooter);

            Log("RAIDOU Remastered Türkçe Yama Kurulum Sihirbazı başlatıldı.");
            Log("Yama kaynak dizini: " + patchRootDir);
        }

        private void Log(string message)
        {
            if (txtLog.InvokeRequired)
            {
                txtLog.Invoke(new Action<string>(Log), message);
                return;
            }
            string timestamp = DateTime.Now.ToString("HH:mm:ss");
            txtLog.AppendText(string.Format("[{0}] {1}{2}", timestamp, message, Environment.NewLine));
            txtLog.SelectionStart = txtLog.Text.Length;
            txtLog.ScrollToCaret();
        }

        private void AutoDetectGamePath()
        {
            // 1. If installer is already placed inside the game directory
            if (IsValidGameDirectory(patchRootDir))
            {
                txtGamePath.Text = patchRootDir;
                Log("Kurulum aracı doğrudan oyun klasörünün içinde algılandı.");
                return;
            }

            // 2. Scan Steam libraries
            List<string> candidates = GetSteamLibraryPaths();
            string[] folderNames = new string[]
            {
                "RAIDOU Remastered The Mystery of the Soulless Army",
                "RAIDOU Remastered",
                "Raidou Remastered",
                "Raidou TMOTSA"
            };

            foreach (string lib in candidates)
            {
                string common = Path.Combine(lib, "steamapps", "common");
                if (!Directory.Exists(common)) continue;

                foreach (string name in folderNames)
                {
                    string candidate = Path.Combine(common, name);
                    if (IsValidGameDirectory(candidate))
                    {
                        txtGamePath.Text = candidate;
                        Log("Oyun klasörü otomatik olarak bulundu: " + candidate);
                        return;
                    }
                }

                // Fallback search for any directory containing Raidou TMOTSA_Data
                try
                {
                    foreach (string dir in Directory.GetDirectories(common, "*Raidou*", SearchOption.TopDirectoryOnly))
                    {
                        if (IsValidGameDirectory(dir))
                        {
                            txtGamePath.Text = dir;
                            Log("Oyun klasörü otomatik olarak bulundu: " + dir);
                            return;
                        }
                    }
                }
                catch { }
            }

            Log("Oyun klasörü otomatik bulunamadı. Lütfen 'Gözat...' butonu ile oyun klasörünü seçin.");
            UpdatePatchStatus();
        }

        private List<string> GetSteamLibraryPaths()
        {
            List<string> paths = new List<string>();
            try
            {
                string steamPath = Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath", null) as string;
                if (string.IsNullOrEmpty(steamPath))
                {
                    steamPath = Registry.GetValue(@"HKEY_CURRENT_USER\Software\Valve\Steam", "SteamPath", null) as string;
                }
                if (!string.IsNullOrEmpty(steamPath))
                {
                    steamPath = steamPath.Replace('/', '\\');
                    paths.Add(steamPath);
                    string vdf = Path.Combine(steamPath, "steamapps", "libraryfolders.vdf");
                    if (File.Exists(vdf))
                    {
                        string content = File.ReadAllText(vdf);
                        foreach (Match m in Regex.Matches(content, "\"path\"\\s+\"([^\"]+)\""))
                        {
                            string libPath = m.Groups[1].Value.Replace("\\\\", "\\");
                            if (!paths.Contains(libPath)) paths.Add(libPath);
                        }
                    }
                }
            }
            catch { }

            foreach (DriveInfo drive in DriveInfo.GetDrives())
            {
                if (!drive.IsReady || drive.DriveType != DriveType.Fixed) continue;
                string[] commonRoots = new string[]
                {
                    Path.Combine(drive.RootDirectory.FullName, "SteamLibrary"),
                    Path.Combine(drive.RootDirectory.FullName, "Program Files (x86)", "Steam"),
                    Path.Combine(drive.RootDirectory.FullName, "Games")
                };
                foreach (string r in commonRoots)
                {
                    if (Directory.Exists(r) && !paths.Contains(r)) paths.Add(r);
                }
            }
            return paths;
        }

        private bool IsValidGameDirectory(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || !Directory.Exists(path)) return false;
            return Directory.Exists(Path.Combine(path, "Raidou TMOTSA_Data"));
        }

        private void UpdatePatchStatus()
        {
            string targetDir = txtGamePath.Text.Trim();
            if (string.IsNullOrEmpty(targetDir) || !Directory.Exists(targetDir))
            {
                lblStatusBadge.Text = "KLASÖR SEÇİLMEDİ";
                lblStatusBadge.ForeColor = Color.FromArgb(200, 200, 210);
                lblStatusBadge.BackColor = Color.FromArgb(45, 45, 55);
                return;
            }

            bool hasDll = File.Exists(Path.Combine(targetDir, "version.dll"));
            bool hasUpdate = Directory.Exists(Path.Combine(targetDir, "update", "Raidou TMOTSA_Data"));

            if (hasDll && hasUpdate)
            {
                lblStatusBadge.Text = "✓ YAMA KURULU";
                lblStatusBadge.ForeColor = Color.FromArgb(110, 240, 145);
                lblStatusBadge.BackColor = Color.FromArgb(25, 60, 40);
            }
            else if (IsValidGameDirectory(targetDir))
            {
                lblStatusBadge.Text = "KURULUMA HAZIR";
                lblStatusBadge.ForeColor = Color.FromArgb(255, 215, 100);
                lblStatusBadge.BackColor = Color.FromArgb(55, 45, 25);
            }
            else
            {
                lblStatusBadge.Text = "KLASÖR DOĞRULANMADI";
                lblStatusBadge.ForeColor = Color.FromArgb(255, 150, 120);
                lblStatusBadge.BackColor = Color.FromArgb(65, 30, 30);
            }
        }

        private void BtnBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dialog = new FolderBrowserDialog())
            {
                dialog.Description = "RAIDOU Remastered oyun klasörünü seçin:";
                if (Directory.Exists(txtGamePath.Text))
                {
                    dialog.SelectedPath = txtGamePath.Text;
                }
                if (dialog.ShowDialog(this) == DialogResult.OK)
                {
                    txtGamePath.Text = dialog.SelectedPath;
                    Log("Seçilen klasör: " + dialog.SelectedPath);
                }
            }
        }

        private async Task InstallPatchAsync()
        {
            string targetDir = txtGamePath.Text.Trim();
            if (string.IsNullOrEmpty(targetDir) || !Directory.Exists(targetDir))
            {
                MessageBox.Show(this, "Lütfen önce geçerli bir oyun klasörü seçin!", "Uyarı", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            string sourceDll = Path.Combine(patchRootDir, "version.dll");
            string sourceUpdateDir = Path.Combine(patchRootDir, "update");

            if (!File.Exists(sourceDll) || !Directory.Exists(sourceUpdateDir))
            {
                MessageBox.Show(this,
                    "Kurulum dosyaları ('version.dll' ve 'update' klasörü) bu programın yanında bulunamadı!\n\nLütfen kurulum aracını yama dosyalarıyla aynı klasörde çalıştırın.",
                    "Eksik Yama Dosyası", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            if (!IsValidGameDirectory(targetDir))
            {
                DialogResult confirm = MessageBox.Show(this,
                    "Seçtiğiniz klasörde 'Raidou TMOTSA_Data' klasörü bulunamadı.\nYine de bu klasöre kurulum yapmak istiyor musunuz?",
                    "Klasör Doğrulama", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (confirm != DialogResult.Yes) return;
            }

            bool sameFolder = string.Equals(
                Path.GetFullPath(patchRootDir).TrimEnd('\\'),
                Path.GetFullPath(targetDir).TrimEnd('\\'),
                StringComparison.OrdinalIgnoreCase);

            if (sameFolder)
            {
                UpdatePatchStatus();
                Log("Yama dosyaları zaten doğrudan oyun klasörünün içinde bulunuyor!");
                MessageBox.Show(this, "Yama dosyaları zaten oyun klasörünün içinde ve kullanıma hazır!", "Bilgi", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            SetButtonsEnabled(false);
            progressBar.Value = 0;

            try
            {
                string[] allUpdateFiles = Directory.GetFiles(sourceUpdateDir, "*", SearchOption.AllDirectories);
                int totalFiles = allUpdateFiles.Length + 1; // +1 for version.dll
                progressBar.Maximum = totalFiles;

                Log("Kurulum başlatılıyor (" + totalFiles + " dosya kopyalanacak)...");

                await Task.Run(() =>
                {
                    int copied = 0;

                    // 1. Copy version.dll
                    string destDll = Path.Combine(targetDir, "version.dll");
                    File.Copy(sourceDll, destDll, true);
                    copied++;
                    ReportProgress(copied, totalFiles, "version.dll kopyalandı");

                    // 2. Copy all files under update/
                    foreach (string srcFile in allUpdateFiles)
                    {
                        string relPath = srcFile.Substring(sourceUpdateDir.Length).TrimStart('\\', '/');
                        string destFile = Path.Combine(targetDir, "update", relPath);
                        string destSubDir = Path.GetDirectoryName(destFile);
                        if (!Directory.Exists(destSubDir))
                        {
                            Directory.CreateDirectory(destSubDir);
                        }
                        File.Copy(srcFile, destFile, true);
                        copied++;
                        ReportProgress(copied, totalFiles, Path.GetFileName(srcFile));
                    }
                });

                // Also write an uninstaller .bat in targetDir
                string uninstallerBat = Path.Combine(targetDir, "Yamayi_Kaldir.bat");
                File.WriteAllText(uninstallerBat,
                    "@echo off\r\nchcp 65001 >nul\r\ncd /d \"%~dp0\"\r\nif exist \"version.dll\" del /f /q \"version.dll\"\r\nif exist \"update\" rmdir /s /q \"update\"\r\necho RAIDOU Remastered Turkce Yama basariyla kaldirildi.\r\npause\r\n");

                lblProgressInfo.Text = "Kurulum başarıyla tamamlandı!";
                Log("✓ Türkçe Yama başarıyla kuruldu!");
                UpdatePatchStatus();

                MessageBox.Show(this,
                    "RAIDOU Remastered Türkçe Yama başarıyla kuruldu!\n\nİyi oyunlar dileriz!",
                    "Kurulum Tamamlandı", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                Log("HATA: " + ex.Message);
                MessageBox.Show(this,
                    "Kurulum sırasında bir hata oluştu (Oyun açıksa lütfen kapatıp tekrar deneyin):\n\n" + ex.Message,
                    "Kurulum Hatası", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        private void ReportProgress(int current, int total, string fileName)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<int, int, string>(ReportProgress), current, total, fileName);
                return;
            }
            progressBar.Value = Math.Min(current, progressBar.Maximum);
            lblProgressInfo.Text = string.Format("Kopyalanıyor ({0}/{1}): {2}", current, total, fileName);
        }

        private void BtnUninstall_Click(object sender, EventArgs e)
        {
            string targetDir = txtGamePath.Text.Trim();
            if (string.IsNullOrEmpty(targetDir) || !Directory.Exists(targetDir))
            {
                MessageBox.Show(this, "Lütfen önce geçerli bir oyun klasörü seçin!", "Uyarı", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            bool sameFolder = string.Equals(
                Path.GetFullPath(patchRootDir).TrimEnd('\\'),
                Path.GetFullPath(targetDir).TrimEnd('\\'),
                StringComparison.OrdinalIgnoreCase);

            string dllPath = Path.Combine(targetDir, "version.dll");
            string updatePath = Path.Combine(targetDir, "update");

            if (!File.Exists(dllPath) && !Directory.Exists(updatePath))
            {
                MessageBox.Show(this, "Seçilen klasörde kurulu bir yama bulunamadı.", "Bilgi", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            if (sameFolder)
            {
                DialogResult warn = MessageBox.Show(this,
                    "Kurulum aracını doğrudan oyun klasörünün içinden çalıştırıyorsunuz.\nYamayı kaldırdığınızda 'version.dll' ve 'update' klasörü silinecektir. Devam etmek istiyor musunuz?",
                    "Yamayı Kaldır", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (warn != DialogResult.Yes) return;
            }

            try
            {
                if (File.Exists(dllPath)) File.Delete(dllPath);
                if (Directory.Exists(updatePath)) Directory.Delete(updatePath, true);

                progressBar.Value = 0;
                lblProgressInfo.Text = "Yama kaldırıldı.";
                Log("✓ Yama dosyaları (version.dll ve update klasörü) başarıyla kaldırıldı.");
                UpdatePatchStatus();

                MessageBox.Show(this, "Türkçe Yama oyun klasöründen başarıyla kaldırıldı.", "Kaldırma Tamamlandı", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                Log("HATA: " + ex.Message);
                MessageBox.Show(this, "Yama kaldırılırken hata oluştu (Oyun açıksa kapatın):\n\n" + ex.Message, "Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void SetButtonsEnabled(bool enabled)
        {
            btnInstall.Enabled = enabled;
            btnUninstall.Enabled = enabled;
            btnBrowse.Enabled = enabled;
            txtGamePath.Enabled = enabled;
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
