# WiFi CSI Indoor Crowd Counting Dataset

A collection of raw WiFi Channel State Information (CSI) recordings for indoor crowd-counting research.

## Download

The dataset contains **95 original `.csi` files**, totaling **3,023,921,749 bytes (3.02 GB / 2.82 GiB)** before compression.

**[Download the complete dataset from Releases](https://github.com/LJYI1/wifi-crowd-counting-dataset/releases/tag/v1.0.0).** Download all four `wifi-crowd-counting-data-*.zip` attachments and extract them into the same directory. Each ZIP is independently extractable. Original filenames and binary contents are preserved.

The green **Code → Download ZIP** button and the automatic **Source code** release archives contain documentation and manifests, not the CSI recordings.

## Collection setup

CSI was collected using the PicoScenes platform, with a TP-Link TL-WDR7660 router as the transmitter and a laptop equipped with an Intel AX210 NIC as the receiver. The acquisition setup used 2 × 2 MIMO, a center frequency of 2.472 GHz, and a channel bandwidth of 20 MHz. Both devices were placed at a height of 1.2 m.

The collection protocol used two indoor environments. Participants walked randomly within the sensing area at approximately 1 m/s. The nominal sampling rate was approximately 60 CSI samples/s, and the nominal recording duration was 120 seconds. These describe the collection protocol; actual duration and sampling rate have not been independently decoded for every released file.

## File organization

Examples: `0per.csi`, `1per_1.csi`, `1per(1).csi`.

The leading integer is recorded as `crowd_count_from_filename` in the manifest. The filenames span **0–18 people**. The suffix-to-session or suffix-to-environment mapping has not been supplied, so environment membership is marked `unknown`. Do not infer a training/test split from filename suffixes.

| Filename-derived count | Files |
| --- | ---: |
| 0 | 3 |
| 1 | 13 |
| 2 | 6 |
| 3 | 7 |
| 4 | 7 |
| 5 | 8 |
| 6 | 6 |
| 7 | 7 |
| 8 | 6 |
| 9 | 6 |
| 10 | 6 |
| 11 | 3 |
| 12 | 5 |
| 13–18 | 2 each |

## Integrity and usage

- `manifest.csv`: original filenames, filename-derived count labels, byte sizes, SHA-256 checksums, and archive membership.
- `SHA256SUMS.txt`: checksums for the extracted recordings.
- `ARCHIVE_SHA256SUMS.txt`: checksums for the ZIP archives.
- `archives.json`: archive sizes, checksums, and file counts.

The `.csi` files are binary recordings. Use a reader compatible with their PicoScenes recording format/version to decode them.

On systems with `sha256sum`, verify downloaded archives with:

```sh
sha256sum -c ARCHIVE_SHA256SUMS.txt
```

After extracting all four ZIPs into one directory, place `SHA256SUMS.txt` in that directory and run:

```sh
sha256sum -c SHA256SUMS.txt
```

PowerShell can check an individual file with `Get-FileHash -Algorithm SHA256 -LiteralPath '1per(1).csi'`; compare the result against the manifest.

## 中文说明

本数据集面向 WiFi 室内人数感知研究，共包含 **95 个原始 CSI 文件，约 3.02 GB**，文件名前缀覆盖 **0–18 人**。请通过上方 **Releases 下载链接**获取全部四个数据 ZIP 包，解压至同一目录。原始文件名和内容保持不变，并提供 SHA-256 校验清单。

采集使用 TP-Link TL-WDR7660 路由器作为发射端，搭载 Intel AX210 网卡的笔记本电脑作为接收端，通过 PicoScenes 记录 CSI。配置为 2×2 MIMO、2.472 GHz 中心频率、20 MHz 带宽，收发设备高度为 1.2 米。采集协议包含两个室内环境，参与者以约 1 米/秒在感知区域内随机行走，标称采样率约 60 次/秒，标称单段时长 120 秒。

上述参数描述采集协议，未逐个解码核实所有记录的实际时长和采样率。清单中的人数标签由文件名提取；后缀与采集环境、批次的对应关系尚未提供，不能据此直接认定训练集或测试集。
