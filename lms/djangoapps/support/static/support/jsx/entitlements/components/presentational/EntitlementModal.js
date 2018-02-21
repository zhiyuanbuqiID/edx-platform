import React from 'react';
import { Modal, Button } from '@edx/paragon';

class EntitlementModal extends React.Component{
	constructor(props){
		super(props)
	}
	submitForm(){
		console.log('submitForm')
		if(this.props.modal.activeEntitlement) {//if there is an active entitlement we are updating an entitlement
			console.log('submitting updateModal')
			const reason = 'dummy reason' //TODO GET THIS VALUE FROM FORM
			const entitlement_uuid = this.props.activeEntitlement.uuid
			const comments = 'dummy comments' //TODO GET THIS VALUES FROM FORM
			this.props.updateEntitlement(reason, entitlement_uuid, comments);
		}
		else { // if there is no active entitlement we are creating a new entitlement
			console.log('submitting creationModal')
			//this.props.createEntitlement(course_uuid, user, mode, reason, comments);
		}

	}
	onClose(){
		console.log('close modal')
		this.props.closeModal();
	}
	render(){
		const title = this.props.modal.activeEntitlement ? "Re-issue Entitlement" : "Create Entitlement"
		
		return (
			<div/>
      	<Modal  open={this.props.modal.modalOpen} 
      	title={title}
	      body="This is a form"
	      buttons={[
	      	<Button
	          label="submit"
	          buttonType="light"
	          onClick = {this.submitForm.bind(this)}/>]},
	      onClose = {this.onClose().bind(this)}/>
   )
	}
}

export default EntitlementModal;
