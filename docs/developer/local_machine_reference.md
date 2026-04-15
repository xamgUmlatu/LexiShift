# Local Machine Reference

Status: active developer reference
Role: Environment / operational reference
Last updated: 2026-03-27
Last verified: 2026-03-27 local Windows inventory check
Purpose: keep one machine-level reference for the current Windows development workstation, including hardware inventory and remote access expectations
Source-of-truth: live OS inventory commands on this host; project behavior truth remains in code, runbooks, and `feature_state_matrix.md`.

Use this page when you need quick context about the current workstation.
Keep project setup and validation commands in `local_setup.md`.

## Executive Summary

- This workstation has ample headroom for day-to-day LexiShift development.
- CPU, RAM, and GPU capacity are not expected to be the limiting factors for local tests, browser debugging, GUI packaging, or docs work.
- A single-monitor `2560x1440` desktop should be practical to drive remotely for code, terminal, and browser tasks.
- Remote productivity risk is primarily network quality, relay use, and session settings rather than host performance.
- RustDesk was not installed on this host at the time of this snapshot.

## Platform Inventory

- Hostname: `DESKTOP-QM3TPCV`
- System vendor / model: OriginPC `GENESIS`
- Operating system: Microsoft Windows 11 Pro 64-bit, build `10.0.26100`
- CPU: Intel Core i9-14900K (`24` cores / `32` logical processors)
- Memory: `102,841,864,192` bytes installed (`95.8 GiB` class usable memory)
- Graphics:
  - Intel UHD Graphics 770
  - NVIDIA GeForce RTX 5080
- Display inventory at check time:
  - `DISPLAY1` primary, `2560x1440`
- Active network adapters at check time:
  - Intel Wi-Fi 6E AX211 (`144 Mbps` reported link speed)
  - NordLynx virtual tunnel adapter present

Treat adapter speed and display state as sampled runtime conditions, not fixed machine limits.

## Development Assessment

- Local development workloads should fit comfortably on this host.
- If a workflow feels slow, investigate I/O, dependency churn, process count, or tool configuration before suspecting raw compute limits.
- The machine is a strong fit for parallel browser + helper + Python test loops.
- The current single-monitor layout is favorable for remote access because there is no mandatory multi-display context switching.

## Remote Access Notes

### RustDesk Suitability

- Expected to be workable for editor, terminal, documentation, dashboard, and light GUI tasks.
- Expected to feel worse for pixel-sensitive UI tuning, frequent drag-heavy workflows, video playback review, or animation-heavy surfaces.
- The host hardware should encode and render comfortably; interactive feel will be dominated by latency and image-compression tradeoffs.
- If the session is routed directly or through a low-latency VPN path, productivity impact should stay moderate.
- If the session falls back to a public relay path or congested Wi-Fi, latency and clarity will degrade first.

### Practical Guidance

- Keep the session to the single primary display when possible.
- If responsiveness matters more than sharpness, scale the remote session down from `2560x1440` toward `1920x1080`.
- For long text-editing sessions, direct/VPN-backed routes are preferable to relay-backed routes.
- Local compile/test/build work still runs at host speed; the slowdown is in interaction, not execution.

## Commands Used For This Snapshot

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory
Get-CimInstance Win32_Processor | Format-List Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed
Get-CimInstance Win32_VideoController | Format-List Name,DriverVersion,AdapterRAM,VideoProcessor
Get-CimInstance Win32_OperatingSystem | Format-List Caption,Version,OSArchitecture
Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name,InterfaceDescription,LinkSpeed
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | Select-Object DeviceName,Bounds,Primary
```
