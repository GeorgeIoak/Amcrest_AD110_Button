# Amcrest_AD110_Button
 Capture doorbell button presses

 
Copy camera-events.service to /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-events.service

In Homes Assistant automation.yaml add

```
- id: "1601758186896"
  alias: Doorbell Rang
  description: When the Amcrest front doorbell button is pushed have an Alexa announcement
  trigger:
    - platform: mqtt
      topic: homeassistant/Doorbell/button
      payload: "on"
  condition: []
  action:
    - service: notify.alexa_media
      data:
        target:
          - media_player.kitchen_echo_show
          - media_player.george_s_echo_show
        data:
          type: announce
        message: Someone is at the front door!
    - service: camera.snapshot
      entity_id: camera.doorbell
      data:
        entity_id: camera.doorbell
        #filename: /media/snapshot_{{ entity_id.name }}{{ now().strftime("%Y-%m-%d.%H.%M") }}.jpg
        # looks like it's an existing issue: https://github.com/home-assistant/core/issues/40241
        # so hard code file name for now
        filename: /media/snapshot_doorbell_{{ now().strftime("%Y-%m-%d.%H.%M") }}.jpg
  mode: single
```
In configuration.yaml add:

```
# amcrest doorbell
amcrest:
  - host: 192.168.10.32
    name: "Doorbell"
    username: !secret amcrest_doorbell_username
    password: !secret amcrest_doorbell_password
    stream_source: rtsp
    binary_sensors:
      - motion_detected
      - online
    sensors:
#      - sdcard
```