import Cocoa

func captureScreenshot() -> NSImage? {
    let displayID = CGMainDisplayID()
    guard let imageRef = CGDisplayCreateImage(displayID) else { return nil }
    let image = NSImage(cgImage: imageRef, size: NSSize.zero)
    return image
}

func saveScreenshot(image: NSImage, to path: String) {
    guard let data = image.tiffRepresentation,
    let bitmapImage = NSBitmapImageRep(data: data),
    let pngData = bitmapImage.representation(using: .png, properties: [:]) else { return }

    do {
        try pngData.write(to: URL(fileURLWithPath: path))
        print("Screenshot saved to \(path)")
    } catch {
        print("Error saving screenshot: \(error)")
    }
}

// Main
let screenshotPath = NSHomeDirectory() + "/screenshot.png"
if let screenshot = captureScreenshot() {
    saveScreenshot(image: screenshot, to: screenshotPath)
} else {
    print("Failed to capture screenshot")
}
