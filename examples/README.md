# LitePipeline - examples

# multiple_actions

this is the basic demo application, there are three actions in it, the third action wait for the first and the second actions finished and received these two actions result, the third action's result as the task's result

# multiple_actions_pyinstaller

functions is the same with the multiple_actions demo application, but, this demo application use pyinstaller to pack the application not venv-pack

# event_actions

functions is the same with the multiple_actions demo application, but, add task fail and success event actions, the event actions will be triggered depend on task result

# generate_actions_dynamically

this is a demo application for demonstrate how to generate actions dynamically, there are two actions when you start it, the first action and the third action, after started, the first action will generate more actions, and, the third action will wait and receive all these actions' result, the third action's result as the task's result

# multiple_actions_forever

this is run forever demo application, you can see the task will never finished, and , you can stop it by command line or UI tool

# multiple_actions_ldfs_output

functions is the same with the multiple_actions demo application, but, this demo application will store the result file on LiteDFS

# pack_application_with_ldfs

this is application not just a demo, it cooperate with litepipeline_pack_tool, let node use it's python environment to pack application for you, therefore you don't need to build up the python environment as the same version as node's

# litepipeline_pack_tool

this is a command line tool, it cooperate with pack_application_with_ldfs application, let node use it's python environment to pack application for you, therefore you don't need to build up the python environment as the same version as node's

this is a python3 package, you can build and install it with command below:
cd ./litepipeline_pack_tool
sudo python3 ./setup.py bdist_wheel # build it
sudo pip3 install ./dist/litepipeline_pack_tool-0.0.2-py3-none-any.whl # install it
sudo pip3 uninstall litepipeline_pack_tool # uninstall it

See more details at litepipeline_pack_tool/README.md
