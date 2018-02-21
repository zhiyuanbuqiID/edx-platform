import React from 'react';
import { Button } from '@edx/paragon';
import SearchContainer from '../container/SearchContainer';
import EntitlementModalContainer from '../container/ModalContainer'

class Main extends React.Component{
	openCreationModal(){
		console.log('create new entitlement')
		this.props.openEntitlementCreationModal()
	}
	constructor(props){
		super(props);
	}
	render(){
		return(
			<div>
				<h1>
					Entitlement Support Page
				</h1>
				<SearchContainer/>
				<Button
			        className={['btn', 'btn-primary']}
			        label= "Create New Entitlement"
			        onClick={this.openCreationModal.bind(this)}/>
			    <EntitlementModalContainer/>
				{React.cloneElement(this.props.children, this.props)}
			</div>
		)
	}
}

export default Main;