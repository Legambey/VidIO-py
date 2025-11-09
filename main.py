import gi
import subprocess

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst

Gst.init(None)

DEFAULT_AUDIO_DEVICE = "alsa_input.usb-ARKMICRO_USB2.0_PC_CAMERA-02.mono-fallback"

def list_video_devices():
    result = subprocess.run(["v4l2-ctl", "--list-devices"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    devices = []
    for line in lines:
        if line.startswith("\t/dev/video"):
            devices.append(line.strip())
    return devices

def list_audio_devices():
    result = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    devices = []
    for line in lines:
        cols = line.split("\t")
        if len(cols) >= 2:
            devices.append((cols[1], cols[1]))
    return devices

class DeviceSelector(Gtk.Dialog):
    def __init__(self):
        super().__init__(title="Sélection des périphériques")
        self.set_modal(True)
        self.set_resizable(False)
        self.set_border_width(10)

        self.video_combo = Gtk.ComboBoxText()
        self.audio_combo = Gtk.ComboBoxText()

        self.video_devices = list_video_devices()
        print("Devices vidéo détectés:", self.video_devices)

        for dev in self.video_devices:
            self.video_combo.append_text(dev)

        self.audio_devices = list_audio_devices()
        selected_audio_index = 0
        for i, (name, dev_id) in enumerate(self.audio_devices):
            self.audio_combo.append_text(name)
            if dev_id == DEFAULT_AUDIO_DEVICE:
                selected_audio_index = i

        self.video_combo.set_active(0 if self.video_devices else -1)
        self.audio_combo.set_active(selected_audio_index if self.audio_devices else -1)

        box = self.get_content_area()
        box.set_spacing(10)
        box.add(Gtk.Label(label="🎥 Source vidéo:"))
        box.add(self.video_combo)
        box.add(Gtk.Label(label="🔊 Source audio:"))
        box.add(self.audio_combo)
        box.add(Gtk.Label(label="👀 Prévisualisation:"))
        self.preview_box = Gtk.Box()
        box.add(self.preview_box)

        self.video_combo.connect("changed", self.on_video_changed)
        self.audio_combo.connect("changed", self.on_audio_changed)

        self.add_button("Valider", Gtk.ResponseType.OK)
        self.show_all()

        if self.video_combo.get_active_text():
            self.start_preview(self.video_combo.get_active_text())

        if self.audio_devices:
            self.start_audio_monitor(self.audio_devices[selected_audio_index][1])

    def on_video_changed(self, combo):
        device = combo.get_active_text()
        if device:
            self.start_preview(device)

    def on_audio_changed(self, combo):
        name = combo.get_active_text()
        for label, dev_id in self.audio_devices:
            if label == name:
                self.start_audio_monitor(dev_id)
                break

    def start_preview(self, device):
        print(f"Démarrage prévisualisation avec device: '{device}'")

        if hasattr(self, "preview_pipeline"):
            self.preview_pipeline.set_state(Gst.State.NULL)
            if hasattr(self, "preview_area"):
                self.preview_box.remove(self.preview_area)

        self.preview_pipeline = Gst.Pipeline.new("preview_pipeline")
        if not self.preview_pipeline:
            print("Erreur: Impossible de créer la pipeline de prévisualisation")
            return

        vsrc = Gst.ElementFactory.make("v4l2src", "video_source")
        vsrc.set_property("device", device)

        decodebin = Gst.ElementFactory.make("decodebin", "decoder")
        videoconvert = Gst.ElementFactory.make("videoconvert", None)
        videobalance = Gst.ElementFactory.make("videobalance", None)
        videobalance.set_property("contrast", 1.0)

        sink = Gst.ElementFactory.make("gtksink", "preview_sink")
        if not sink:
            sink = Gst.ElementFactory.make("autovideosink", "preview_sink")
            if not sink:
                print("Erreur: Aucun sink vidéo disponible")
                return

        for el in [vsrc, decodebin, videoconvert, videobalance, sink]:
            self.preview_pipeline.add(el)

        if not vsrc.link(decodebin):
            print("Erreur: Impossible de linker v4l2src vers decodebin")
            return

        if not videoconvert.link(videobalance):
            print("Erreur: Impossible de linker videoconvert vers videobalance")
            return

        if not videobalance.link(sink):
            print("Erreur: Impossible de linker videobalance vers sink")
            return

        def on_pad_added(decodebin, pad):
            sink_pad = videoconvert.get_static_pad("sink")
            if not sink_pad.is_linked():
                pad.link(sink_pad)
        decodebin.connect("pad-added", on_pad_added)

        self.preview_area = sink.get_property("widget")
        self.preview_box.pack_start(self.preview_area, True, True, 0)
        self.preview_area.show()

        self.preview_pipeline.set_state(Gst.State.PLAYING)

    def start_audio_monitor(self, device):
        print(f"Démarrage préaudition avec device audio: '{device}'")

        if hasattr(self, "audio_monitor_pipeline"):
            self.audio_monitor_pipeline.set_state(Gst.State.NULL)
            del self.audio_monitor_pipeline

        self.audio_monitor_pipeline = Gst.Pipeline.new("audio_monitor_pipeline")

        asrc = Gst.ElementFactory.make("pulsesrc", "audio_source")
        asrc.set_property("device", device)

        volume = Gst.ElementFactory.make("volume", None)
        volume.set_property("volume", 0.5)

        resample = Gst.ElementFactory.make("audioresample", None)
        sink = Gst.ElementFactory.make("autoaudiosink", None)
        sink.set_property("sync", False)

        for el in [asrc, volume, resample, sink]:
            if not el:
                print(f"Erreur: Élément manquant pour la préaudition")
                return
            self.audio_monitor_pipeline.add(el)

        asrc.link(volume)
        volume.link(resample)
        resample.link(sink)

        self.audio_monitor_pipeline.set_state(Gst.State.PLAYING)

    def get_selected_devices(self):
        video = self.video_combo.get_active_text()
        audio = self.audio_combo.get_active_text()
        return video, audio

    def destroy(self):
        if hasattr(self, "preview_pipeline"):
            self.preview_pipeline.set_state(Gst.State.NULL)
        if hasattr(self, "audio_monitor_pipeline"):
            self.audio_monitor_pipeline.set_state(Gst.State.NULL)
        super().destroy()

class Window(Gtk.Window):
    def __init__(self, video_device, audio_device):
        super().__init__(title="VidIO")

        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.box = Gtk.Box()
        self.add(self.box)

        self.pipeline = Gst.Pipeline.new("pipeline")

        self.vsrc = Gst.ElementFactory.make("v4l2src", "video_source")
        self.vsrc.set_property("device", video_device)

        self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
        self.decodebin.connect("pad-added", self.on_pad_added)

        self.videoconvert = Gst.ElementFactory.make("videoconvert", None)
        self.videobalance = Gst.ElementFactory.make("videobalance", None)
        self.videobalance.set_property("contrast", 2)

        self.gtksink = Gst.ElementFactory.make("gtksink", "gtksink")

        self.asrc = Gst.ElementFactory.make("pulsesrc", "audio_source")
        self.asrc.set_property("device", audio_device)

        self.volume = Gst.ElementFactory.make("volume", None)
        self.volume.set_property("volume", 0.5)

        self.audioresample = Gst.ElementFactory.make("audioresample", None)
        self.audiosink = Gst.ElementFactory.make("autoaudiosink", None)
        self.audiosink.set_property("sync", False)

        for el in [
            self.vsrc, self.decodebin, self.videoconvert, self.videobalance, self.gtksink,
            self.asrc, self.volume, self.audioresample, self.audiosink
        ]:
            self.pipeline.add(el)

        if not self.vsrc.link(self.decodebin):
            print("Erreur: Impossible de linker v4l2src vers decodebin")
            return

        if not self.videoconvert.link(self.videobalance):
            print("Erreur: Impossible de linker videoconvert vers videobalance")
            return

        if not self.videobalance.link(self.gtksink):
            print("Erreur: Impossible de linker videobalance vers gtksink")
            return

        if not self.asrc.link(self.volume):
            print("Erreur: Impossible de linker pulsesrc vers volume")
            return

        if not self.volume.link(self.audioresample):
            print("Erreur: Impossible de linker volume vers audioresample")
            return

        if not self.audioresample.link(self.audiosink):
            print("Erreur: Impossible de linker audioresample vers audiosink")
            return

        self.box.pack_start(self.gtksink.props.widget, True, True, 0)

        self.connect("destroy", self.quit)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_pad_added(self, decodebin, pad):
        sink_pad = self.videoconvert.get_static_pad("sink")
        if not sink_pad.is_linked():
            pad.link(sink_pad)

            caps = pad.get_current_caps()
            if caps:
                structure = caps.get_structure(0)
                width = structure.get_value('width')
                height = structure.get_value('height')

                if width and height:
                    self.set_default_size(width, height)
                    self.resize(width, height)

    def quit(self, *args):
        self.pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

if __name__ == "__main__":
    selector = DeviceSelector()
    response = selector.run()

    if response == Gtk.ResponseType.OK:
        video_device, audio_device = selector.get_selected_devices()
        print(f"Device vidéo sélectionné: '{video_device}'")
        print(f"Device audio sélectionné: '{audio_device}'")
        selector.destroy()

        win = Window(video_device, audio_device)
        win.show_all()
        Gtk.main()
    else:
        selector.destroy()
