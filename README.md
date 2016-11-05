# FOMT-Prototype
This is  sample for AU China 2016. It demos the basic scenarios of Future of Making Things (FOMT). How we connect customer, designer, vendor and machining.

## Live demo
1. The demo videos are available at [BOX](https://autodesk.boxcn.net/s/f1n11j4hkqv5nqmkiqkk1kl4ncevc62m).
  * demo-with-mobile.mp4 : taken by my iPhone video, that contains the demo on the mobile
  * demo-without-mobile.mp4: taken on PC only
2. Demo Steps
  Firstly, load the plugin of Fusion 360. Switch to Model environment. The menus will be loaded. The presenter is a designer. 3 scenarios:
	
  1) In the browser, type http://au-china-forge.herokuapp.com/en/aumain.html with odd number, say #1. The role is customer. The presenter open any model. It is recommended to open those in built-in Repositories of Fusion Model Samples >> CAM Samples.  The presenter sends the model to the customer. The customer can review the information and 3D model.   
  Open another browser, log in with even number which is adjacent to the customer, say #2. The role is vendor. 
  After the customer is fine with the information, he can start RFQ, then the vendor. Then the vendor can also review the information and check if they can provide the service and produce the part.
 
  2)	Similar to #1, but the presenter will log in with number #0. The presenter sends the model to the webpage. So when presenter clicks RFQ, all vendors can get the notification. They can start to bid. The bid value is a random value which means how much the cost is. In the page of presenter, bid table will be shown up.
 
 3) Similar to #2, but a click the first button of Fusion plugin to generate a chair, next click any other button to generate carving curves. Then the model with g-code will be sent to the customer, next to vendor. The customer can click CNC button, the simulation process of CNC will run in the viewer of vendor’s page.    
