import Cocoa

var globalEventMonitor: Any?

func captureScreenshot() -> NSImage? {
    let displayID = CGMainDisplayID()
    guard let imageRef = CGDisplayCreateImage(displayID) else {
        print("Failed to create image from display.")
        return nil
    }
    let image = NSImage(cgImage: imageRef, size: NSSize.zero)
    print("Screenshot captured.")
    return image
}

func saveScreenshot(image: NSImage, to path: String) {
    guard let data = image.tiffRepresentation,
    let bitmapImage = NSBitmapImageRep(data: data),
    let pngData = bitmapImage.representation(using: .png, properties: [:]) else {
        print("Failed to convert image to PNG data.")
        return
    }

    do {
        try pngData.write(to: URL(fileURLWithPath: path))
        print("Screenshot saved to \(path)")
    } catch {
        print("Error saving screenshot: \(error)")
    }
}

func setupGlobalHotKey() {
    let mask: NSEvent.ModifierFlags = [.control, .command]
    globalEventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { (event) in
        print("Key down event detected.")
        if event.modifierFlags.contains(mask) && event.charactersIgnoringModifiers == "k" {
            print("Ctrl + Command + K pressed.")
            if let screenshot = captureScreenshot() {
                let screenshotPath = NSHomeDirectory() + "/screenshot.png"
                saveScreenshot(image: screenshot, to: screenshotPath)
            } else {
                print("Failed to capture screenshot.")
            }
        }
    }
}

// Main
setupGlobalHotKey()
RunLoop.main.run()
