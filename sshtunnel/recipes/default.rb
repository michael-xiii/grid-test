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

# @todo move to config
key_url = 'http://127.0.0.1/id_dsa.pub'



bash "install_pips" do
  code <<-RUN_CODE
  pip install procname simplejson
  RUN_CODE
end

remote_file "./id_dsa.pub" do
  source key_url
  mode "0644"
end

bash "create_ssh_dir" do
  code <<-MKDIR_CODE
  mkdir -p ~/.ssh
  MKDIR_CODE
end


# @todo check if key exists
bash "append_public_key" do
  code <<-ADD_KEY_CODE
  cat ./id_dsa.pub >> ~/.ssh/authorized_keys
  ADD_KEY_CODE
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

