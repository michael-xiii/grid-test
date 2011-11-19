#
# Cookbook Name:: sshtunnel
# Recipe:: default
#
# Copyright 2011, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

package "sudo" 
package "python"
package "python-dev"
package "python-twisted"
package "python-pip" 
package "python-MySQLDb"


bash "install_pips" do
  code <<-RUN_CODE
  pip install procname simplejson
  RUN_CODE
end

git "/var/sshtunnel" do
  repository "git://github.com/michael-xiii/grid-test.git"
  reference "master"
  action :checkout
end

bash "run service" do
  code <<-RUN_CODE
  sudo /var/sshtunnel/SSHTunnelManager/sshtunneld restart
  RUN_CODE
end

