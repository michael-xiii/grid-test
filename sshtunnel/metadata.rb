maintainer       "YOUR_COMPANY_NAME"
maintainer_email "michael.neradkov+git@gmail.com"
license          "All rights reserved" 
description      "Installs/Configures sshtunnel service"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.rdoc'))
version          "0.0.1"

%w{ fedora redhat centos ubuntu debian }.each do |os|
  supports os
end